"""
Content Generation Routes
=========================
API endpoints for generating social media content using LLM.

Endpoints:
- POST /api/generate - Generate content for a topic
- GET /api/topics - List all topics
- GET /api/topics/{id} - Get a specific topic with its posts
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Topic, GeneratedPost, Platform, PostStatus
from app.services.llm_client import get_llm_client, LLMError

# Create router
router = APIRouter(prefix="/api", tags=["Content Generation"])


# =========================================
# Pydantic Models (Request/Response Schemas)
# =========================================
class GenerateRequest(BaseModel):
    """Request body for content generation."""
    topic: str = Field(..., min_length=3, max_length=500, description="The topic to generate content about")
    platforms: List[str] = Field(
        default=["linkedin", "instagram", "facebook"],
        description="Target platforms (linkedin, instagram, facebook)"
    )
    additional_context: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional additional context for the LLM"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "platforms": ["linkedin", "instagram", "facebook"],
                "additional_context": "Focus on practical applications for beginners"
            }
        }


class GeneratedContentResponse(BaseModel):
    """Response for a single generated post."""
    platform: str
    content: str
    hashtags: Optional[List[str]] = None
    post_id: int
    status: str


class GenerateResponse(BaseModel):
    """Response body for content generation."""
    topic_id: int
    topic_name: str
    posts: List[GeneratedContentResponse]
    created_at: str


class TopicResponse(BaseModel):
    """Response for a single topic."""
    id: int
    name: str
    description: Optional[str]
    created_at: str
    post_count: int


class PostDetailResponse(BaseModel):
    """Detailed response for a single post."""
    id: int
    platform: str
    content: str
    hashtags: Optional[str]
    status: str
    scheduled_time: Optional[str]
    posted_at: Optional[str]
    created_at: str


class TopicDetailResponse(BaseModel):
    """Response for a topic with all its posts."""
    id: int
    name: str
    description: Optional[str]
    created_at: str
    posts: List[PostDetailResponse]


# =========================================
# API Endpoints
# =========================================
@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate social media content for a given topic.
    
    This endpoint:
    1. Creates a new topic in the database
    2. Uses the LLM to generate platform-specific content
    3. Stores generated content as draft posts
    4. Returns all generated content for preview
    
    The posts are created with status=DRAFT and must be approved
    before scheduling.
    """
    # Validate platforms
    valid_platforms = {"linkedin", "instagram", "facebook"}
    requested_platforms = set(p.lower() for p in request.platforms)
    invalid = requested_platforms - valid_platforms
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platforms: {invalid}. Valid options: {valid_platforms}"
        )
    
    # Create topic
    topic = Topic(
        name=request.topic,
        description=request.additional_context
    )
    db.add(topic)
    db.flush()  # Get the topic ID without committing
    
    # Generate content for each platform
    generated_posts = []
    
    try:
        llm_client = get_llm_client()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    
    for platform_name in requested_platforms:
        platform = Platform(platform_name)
        
        try:
            # Generate content using LLM
            result = llm_client.generate_content(
                topic=request.topic,
                platform=platform,
                additional_context=request.additional_context
            )
            
            # Create post record
            post = GeneratedPost(
                topic_id=topic.id,
                platform=platform,
                content=result["content"],
                hashtags=",".join(result.get("hashtags", [])),
                status=PostStatus.DRAFT
            )
            db.add(post)
            db.flush()
            
            generated_posts.append(GeneratedContentResponse(
                platform=platform.value,
                content=result["content"],
                hashtags=result.get("hashtags"),
                post_id=post.id,
                status=PostStatus.DRAFT.value
            ))
            
        except LLMError as e:
            # Log error but continue with other platforms
            generated_posts.append(GeneratedContentResponse(
                platform=platform_name,
                content=f"Error generating content: {str(e)}",
                hashtags=[],
                post_id=0,
                status="error"
            ))
    
    # Commit all changes
    db.commit()
    
    return GenerateResponse(
        topic_id=topic.id,
        topic_name=topic.name,
        posts=generated_posts,
        created_at=topic.created_at.isoformat()
    )


@router.get("/topics", response_model=List[TopicResponse])
async def list_topics(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all topics with their post counts.
    
    Supports pagination via skip and limit parameters.
    """
    topics = db.query(Topic).order_by(Topic.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        TopicResponse(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            created_at=topic.created_at.isoformat(),
            post_count=len(topic.posts)
        )
        for topic in topics
    ]


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse)
async def get_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific topic with all its generated posts.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found"
        )
    
    return TopicDetailResponse(
        id=topic.id,
        name=topic.name,
        description=topic.description,
        created_at=topic.created_at.isoformat(),
        posts=[
            PostDetailResponse(
                id=post.id,
                platform=post.platform.value,
                content=post.content,
                hashtags=post.hashtags,
                status=post.status.value,
                scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
                posted_at=post.posted_at.isoformat() if post.posted_at else None,
                created_at=post.created_at.isoformat()
            )
            for post in topic.posts
        ]
    )


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a topic and all its associated posts.
    
    This is a destructive action and cannot be undone.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic {topic_id} not found"
        )
    
    db.delete(topic)
    db.commit()
