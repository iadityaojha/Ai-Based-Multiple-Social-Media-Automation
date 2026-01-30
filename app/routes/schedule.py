"""
Scheduling Routes
=================
API endpoints for managing post scheduling and publishing.

Endpoints:
- GET /api/posts - List all posts with optional filters
- GET /api/posts/{id} - Get a specific post
- POST /api/posts/{id}/approve - Approve and optionally schedule a post
- POST /api/posts/{id}/schedule - Schedule a post for a specific time
- DELETE /api/posts/{id} - Cancel/delete a post
- POST /api/posts/{id}/publish-now - Immediately publish a post
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GeneratedPost, PostStatus, Platform, ErrorLog
from app.scheduler import post_scheduler

# Create router
router = APIRouter(prefix="/api", tags=["Scheduling"])


# =========================================
# Pydantic Models (Request/Response Schemas)
# =========================================
class ScheduleRequest(BaseModel):
    """Request body for scheduling a post."""
    scheduled_time: Optional[datetime] = Field(
        None,
        description="When to publish. If not provided, post will be queued for immediate publishing."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "scheduled_time": "2025-01-31T10:00:00Z"
            }
        }


class PostResponse(BaseModel):
    """Response for a single post."""
    id: int
    topic_id: int
    topic_name: str
    platform: str
    content: str
    hashtags: Optional[str]
    status: str
    scheduled_time: Optional[str]
    posted_at: Optional[str]
    retry_count: int
    created_at: str
    updated_at: str


class PostListResponse(BaseModel):
    """Response for listing posts."""
    total: int
    posts: List[PostResponse]


class ErrorLogResponse(BaseModel):
    """Response for an error log entry."""
    id: int
    error_message: str
    error_type: Optional[str]
    attempt_number: int
    created_at: str


class PostDetailResponse(PostResponse):
    """Detailed response for a post including error logs."""
    error_logs: List[ErrorLogResponse]


class ApproveRequest(BaseModel):
    """Request body for approving a post."""
    scheduled_time: Optional[datetime] = Field(
        None,
        description="Optional scheduled time. If not provided, post is queued for immediate publishing."
    )


class UpdateContentRequest(BaseModel):
    """Request body for updating post content."""
    content: str = Field(..., min_length=1, description="Updated post content")
    hashtags: Optional[str] = Field(None, description="Updated hashtags (comma-separated)")


# =========================================
# API Endpoints
# =========================================
@router.get("/posts", response_model=PostListResponse)
async def list_posts(
    status_filter: Optional[str] = Query(None, description="Filter by status: draft, pending, posted, failed"),
    platform_filter: Optional[str] = Query(None, description="Filter by platform: linkedin, instagram, facebook"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all posts with optional filters.
    
    Supports filtering by status and platform, and pagination.
    """
    query = db.query(GeneratedPost)
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = PostStatus(status_filter.lower())
            query = query.filter(GeneratedPost.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid options: draft, pending, posted, failed"
            )
    
    # Apply platform filter
    if platform_filter:
        try:
            platform_enum = Platform(platform_filter.lower())
            query = query.filter(GeneratedPost.platform == platform_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {platform_filter}. Valid options: linkedin, instagram, facebook"
            )
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    posts = query.order_by(GeneratedPost.created_at.desc()).offset(skip).limit(limit).all()
    
    return PostListResponse(
        total=total,
        posts=[
            PostResponse(
                id=post.id,
                topic_id=post.topic_id,
                topic_name=post.topic.name,
                platform=post.platform.value,
                content=post.content,
                hashtags=post.hashtags,
                status=post.status.value,
                scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
                posted_at=post.posted_at.isoformat() if post.posted_at else None,
                retry_count=post.retry_count,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat()
            )
            for post in posts
        ]
    )


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific post with its error logs.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    return PostDetailResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        status=post.status.value,
        scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
        error_logs=[
            ErrorLogResponse(
                id=log.id,
                error_message=log.error_message,
                error_type=log.error_type,
                attempt_number=log.attempt_number,
                created_at=log.created_at.isoformat()
            )
            for log in post.error_logs
        ]
    )


@router.post("/posts/{post_id}/approve", response_model=PostResponse)
async def approve_post(
    post_id: int,
    request: ApproveRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a draft post for publishing.
    
    Changes status from DRAFT to PENDING and optionally sets a schedule time.
    Once approved, the scheduler will pick it up for publishing.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post has already been published"
        )
    
    # Update post status
    post.status = PostStatus.PENDING
    post.scheduled_time = request.scheduled_time
    post.retry_count = 0  # Reset retry count
    db.commit()
    
    return PostResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        status=post.status.value,
        scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.post("/posts/{post_id}/schedule", response_model=PostResponse)
async def schedule_post(
    post_id: int,
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a post for a specific time.
    
    If the post is in DRAFT status, it will be automatically approved.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post has already been published"
        )
    
    # Validate scheduled time is in the future
    if request.scheduled_time and request.scheduled_time <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Update post
    post.status = PostStatus.PENDING
    post.scheduled_time = request.scheduled_time
    post.retry_count = 0
    db.commit()
    
    return PostResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        status=post.status.value,
        scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a post.
    
    Cannot delete posts that have already been published.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a post that has already been published"
        )
    
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/cancel", response_model=PostResponse)
async def cancel_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a scheduled post.
    
    Changes status back to DRAFT and clears the scheduled time.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a post that has already been published"
        )
    
    post.status = PostStatus.DRAFT
    post.scheduled_time = None
    db.commit()
    
    return PostResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        status=post.status.value,
        scheduled_time=None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post_content(
    post_id: int,
    request: UpdateContentRequest,
    db: Session = Depends(get_db)
):
    """
    Update the content of a post.
    
    Only draft posts can be edited.
    """
    post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    
    if post.status != PostStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft posts can be edited"
        )
    
    post.content = request.content
    if request.hashtags is not None:
        post.hashtags = request.hashtags
    db.commit()
    
    return PostResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        status=post.status.value,
        scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get posting statistics.
    """
    draft_count = db.query(GeneratedPost).filter(GeneratedPost.status == PostStatus.DRAFT).count()
    pending_count = db.query(GeneratedPost).filter(GeneratedPost.status == PostStatus.PENDING).count()
    posted_count = db.query(GeneratedPost).filter(GeneratedPost.status == PostStatus.POSTED).count()
    failed_count = db.query(GeneratedPost).filter(GeneratedPost.status == PostStatus.FAILED).count()
    
    return {
        "draft": draft_count,
        "pending": pending_count,
        "posted": posted_count,
        "failed": failed_count,
        "total": draft_count + pending_count + posted_count + failed_count
    }
