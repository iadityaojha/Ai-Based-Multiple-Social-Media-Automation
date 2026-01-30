"""
Content Generation Routes (Per-User)
=====================================
Generate AI content using user's own LLM API keys.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Topic, GeneratedPost, Platform, PostStatus, ToneStyle
from app.auth import get_current_user
from app.services.llm_client import get_user_llm_client, LLMError

router = APIRouter(prefix="/api/generate", tags=["Content Generation"])


# =========================================
# Schemas
# =========================================
class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    platforms: List[str] = Field(default=["linkedin", "instagram", "facebook"])
    tone: str = Field(default="professional")
    additional_context: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "platforms": ["linkedin", "instagram", "facebook"],
                "tone": "professional",
                "additional_context": "Focus on practical applications"
            }
        }


class GeneratedContentItem(BaseModel):
    platform: str
    content: str
    hashtags: List[str]
    post_id: int
    status: str


class GenerateResponse(BaseModel):
    topic_id: int
    topic_name: str
    posts: List[GeneratedContentItem]


class TopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tone: str
    created_at: str
    post_count: int


class PostResponse(BaseModel):
    id: int
    platform: str
    content: str
    hashtags: Optional[str]
    tone: str
    status: str
    scheduled_time: Optional[str]
    posted_at: Optional[str]
    created_at: str


# =========================================
# Routes
# =========================================
@router.post("/", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    data: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI content for multiple platforms.
    Uses the user's own LLM API key.
    """
    # Validate platforms
    valid_platforms = {"linkedin", "instagram", "facebook"}
    platforms = set(p.lower() for p in data.platforms)
    invalid = platforms - valid_platforms
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platforms: {invalid}"
        )
    
    # Validate tone
    try:
        tone = ToneStyle(data.tone.lower())
    except ValueError:
        valid_tones = [t.value for t in ToneStyle]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tone. Valid options: {valid_tones}"
        )
    
    # Get user's LLM client
    try:
        llm_client = get_user_llm_client(user, db)
    except LLMError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Create topic
    topic = Topic(
        user_id=user.id,
        name=data.topic,
        description=data.additional_context,
        tone=tone
    )
    db.add(topic)
    db.flush()
    
    # Generate content for each platform
    generated_posts = []
    
    for platform_name in platforms:
        platform = Platform(platform_name)
        
        try:
            result = llm_client.generate_content(
                topic=data.topic,
                platform=platform,
                tone=tone,
                additional_context=data.additional_context
            )
            
            post = GeneratedPost(
                user_id=user.id,
                topic_id=topic.id,
                platform=platform,
                content=result["content"],
                hashtags=",".join(result.get("hashtags", [])),
                tone=tone,
                status=PostStatus.DRAFT
            )
            db.add(post)
            db.flush()
            
            generated_posts.append(GeneratedContentItem(
                platform=platform.value,
                content=result["content"],
                hashtags=result.get("hashtags", []),
                post_id=post.id,
                status=PostStatus.DRAFT.value
            ))
            
        except LLMError as e:
            generated_posts.append(GeneratedContentItem(
                platform=platform_name,
                content=f"Error: {str(e)}",
                hashtags=[],
                post_id=0,
                status="error"
            ))
    
    db.commit()
    
    return GenerateResponse(
        topic_id=topic.id,
        topic_name=topic.name,
        posts=generated_posts
    )


@router.get("/topics", response_model=List[TopicResponse])
async def list_topics(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all topics for the current user."""
    topics = db.query(Topic).filter(
        Topic.user_id == user.id
    ).order_by(Topic.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        TopicResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            tone=t.tone.value,
            created_at=t.created_at.isoformat(),
            post_count=len(t.posts)
        )
        for t in topics
    ]


@router.get("/topics/{topic_id}")
async def get_topic(
    topic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a topic with all its posts."""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return {
        "id": topic.id,
        "name": topic.name,
        "description": topic.description,
        "tone": topic.tone.value,
        "created_at": topic.created_at.isoformat(),
        "posts": [
            PostResponse(
                id=p.id,
                platform=p.platform.value,
                content=p.content,
                hashtags=p.hashtags,
                tone=p.tone.value,
                status=p.status.value,
                scheduled_time=p.scheduled_time.isoformat() if p.scheduled_time else None,
                posted_at=p.posted_at.isoformat() if p.posted_at else None,
                created_at=p.created_at.isoformat()
            )
            for p in topic.posts
        ]
    }


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a topic and all its posts."""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == user.id
    ).first()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    db.delete(topic)
    db.commit()
