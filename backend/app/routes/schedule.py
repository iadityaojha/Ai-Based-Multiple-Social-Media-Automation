"""
Scheduling Routes (Per-User)
============================
Manage post scheduling and publishing for each user.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GeneratedPost, PostStatus, Platform, ErrorLog
from app.auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["Scheduling"])


# =========================================
# Schemas
# =========================================
class ScheduleRequest(BaseModel):
    scheduled_time: Optional[datetime] = None


class UpdatePostRequest(BaseModel):
    content: str = Field(..., min_length=1)
    hashtags: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    platform: str
    content: str
    hashtags: Optional[str]
    tone: str
    status: str
    scheduled_time: Optional[str]
    posted_at: Optional[str]
    retry_count: int
    last_error: Optional[str]
    created_at: str
    updated_at: str


class PostListResponse(BaseModel):
    total: int
    posts: List[PostResponse]


class StatsResponse(BaseModel):
    draft: int
    pending: int
    posted: int
    failed: int
    total: int


class ErrorLogItem(BaseModel):
    id: int
    error_message: str
    error_type: Optional[str]
    attempt_number: int
    created_at: str


# =========================================
# Helper
# =========================================
def post_to_response(post: GeneratedPost) -> PostResponse:
    return PostResponse(
        id=post.id,
        topic_id=post.topic_id,
        topic_name=post.topic.name,
        platform=post.platform.value,
        content=post.content,
        hashtags=post.hashtags,
        tone=post.tone.value,
        status=post.status.value,
        scheduled_time=post.scheduled_time.isoformat() if post.scheduled_time else None,
        posted_at=post.posted_at.isoformat() if post.posted_at else None,
        retry_count=post.retry_count,
        last_error=post.last_error,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


# =========================================
# Routes
# =========================================
@router.get("/", response_model=PostListResponse)
async def list_posts(
    status_filter: Optional[str] = Query(None),
    platform_filter: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all posts for the current user."""
    query = db.query(GeneratedPost).filter(GeneratedPost.user_id == user.id)
    
    if status_filter:
        try:
            query = query.filter(GeneratedPost.status == PostStatus(status_filter.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status filter")
    
    if platform_filter:
        try:
            query = query.filter(GeneratedPost.platform == Platform(platform_filter.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid platform filter")
    
    total = query.count()
    posts = query.order_by(GeneratedPost.created_at.desc()).offset(skip).limit(limit).all()
    
    return PostListResponse(
        total=total,
        posts=[post_to_response(p) for p in posts]
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get posting statistics for the current user."""
    base = db.query(GeneratedPost).filter(GeneratedPost.user_id == user.id)
    
    return StatsResponse(
        draft=base.filter(GeneratedPost.status == PostStatus.DRAFT).count(),
        pending=base.filter(GeneratedPost.status == PostStatus.PENDING).count(),
        posted=base.filter(GeneratedPost.status == PostStatus.POSTED).count(),
        failed=base.filter(GeneratedPost.status == PostStatus.FAILED).count(),
        total=base.count()
    )


@router.get("/upcoming")
async def get_upcoming_posts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming scheduled posts."""
    posts = db.query(GeneratedPost).filter(
        GeneratedPost.user_id == user.id,
        GeneratedPost.status == PostStatus.PENDING,
        GeneratedPost.scheduled_time != None
    ).order_by(GeneratedPost.scheduled_time.asc()).limit(20).all()
    
    return {"posts": [post_to_response(p) for p in posts]}


@router.get("/{post_id}")
async def get_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post with error logs."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    response = post_to_response(post)
    return {
        **response.model_dump(),
        "error_logs": [
            ErrorLogItem(
                id=log.id,
                error_message=log.error_message,
                error_type=log.error_type,
                attempt_number=log.attempt_number,
                created_at=log.created_at.isoformat()
            )
            for log in post.error_logs
        ]
    }


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    data: UpdatePostRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update post content."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status not in [PostStatus.DRAFT, PostStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Can only edit draft or failed posts")
    
    post.content = data.content
    if data.hashtags is not None:
        post.hashtags = data.hashtags
    
    db.commit()
    db.refresh(post)
    
    return post_to_response(post)


@router.post("/{post_id}/approve", response_model=PostResponse)
async def approve_post(
    post_id: int,
    data: ScheduleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve and schedule a post."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(status_code=400, detail="Post already published")
    
    post.status = PostStatus.PENDING
    post.scheduled_time = data.scheduled_time
    post.retry_count = 0
    post.last_error = None
    
    db.commit()
    db.refresh(post)
    
    return post_to_response(post)


@router.post("/{post_id}/cancel", response_model=PostResponse)
async def cancel_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled post."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(status_code=400, detail="Cannot cancel published post")
    
    post.status = PostStatus.DRAFT
    post.scheduled_time = None
    
    db.commit()
    db.refresh(post)
    
    return post_to_response(post)


@router.post("/{post_id}/retry", response_model=PostResponse)
async def retry_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry a failed post."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status != PostStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed posts can be retried")
    
    post.status = PostStatus.PENDING
    post.retry_count = 0
    post.last_error = None
    
    db.commit()
    db.refresh(post)
    
    return post_to_response(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post."""
    post = db.query(GeneratedPost).filter(
        GeneratedPost.id == post_id,
        GeneratedPost.user_id == user.id
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.status == PostStatus.POSTED:
        raise HTTPException(status_code=400, detail="Cannot delete published post")
    
    db.delete(post)
    db.commit()
