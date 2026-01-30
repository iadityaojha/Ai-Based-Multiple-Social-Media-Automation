"""
Manual Post Routes
==================
Create and post user-written content with optional image upload.
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GeneratedPost, Topic, Platform, PostStatus, ToneStyle
from app.auth import get_current_user
from app.services import get_linkedin_service, get_instagram_service, get_facebook_service

router = APIRouter(prefix="/api/manual-post", tags=["Manual Post"])

# Create uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================
# Pydantic Schemas
# =========================================
class ManualPostCreate(BaseModel):
    content: str
    platforms: List[str]  # ['linkedin', 'instagram', 'facebook']
    image_path: Optional[str] = None
    schedule_time: Optional[datetime] = None


class ManualPostResponse(BaseModel):
    success: bool
    message: str
    posts: List[dict] = []


# =========================================
# Routes
# =========================================
@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Upload an image for a manual post."""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB."
        )
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{user.id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(file_content)
    
    return {
        "success": True,
        "filename": filename,
        "path": f"/api/manual-post/images/{filename}",
        "size": len(file_content)
    }


@router.get("/images/{filename}")
async def get_image(filename: str):
    """Serve uploaded images."""
    from fastapi.responses import FileResponse
    
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(filepath)


@router.post("/", response_model=ManualPostResponse)
async def create_manual_post(
    content: str = Form(...),
    platforms: str = Form(...),  # Comma-separated: "linkedin,instagram,facebook"
    image_filename: Optional[str] = Form(None),
    schedule_time: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a manual post and optionally post it immediately to selected platforms.
    """
    platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    
    if not platform_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one platform must be selected"
        )
    
    valid_platforms = ["linkedin", "instagram", "facebook"]
    for p in platform_list:
        if p not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {p}. Valid options: {valid_platforms}"
            )
    
    # Get image path if provided
    image_path = None
    if image_filename:
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        if not os.path.exists(image_path):
            image_path = None
    
    # Parse schedule time if provided
    scheduled_dt = None
    if schedule_time:
        try:
            scheduled_dt = datetime.fromisoformat(schedule_time.replace("Z", "+00:00"))
        except ValueError:
            pass
    
    # Create a topic for this manual post
    topic = Topic(
        user_id=user.id,
        name=f"Manual Post - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        description="Manually created post",
        tone=ToneStyle.PROFESSIONAL
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    
    # Create posts for each platform
    results = []
    created_posts = []
    
    for platform_str in platform_list:
        platform = Platform(platform_str)
        
        # Determine status based on scheduling
        if scheduled_dt:
            post_status = PostStatus.PENDING
        else:
            post_status = PostStatus.PENDING  # Will try to post immediately
        
        # Create the post record
        post = GeneratedPost(
            user_id=user.id,
            topic_id=topic.id,
            platform=platform,
            content=content,
            hashtags="",
            tone=ToneStyle.PROFESSIONAL,
            status=post_status,
            scheduled_time=scheduled_dt
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        created_posts.append(post)
        
        # If no schedule time, try to post immediately
        if not scheduled_dt:
            try:
                post_result = await _post_to_platform(
                    platform=platform,
                    content=content,
                    image_path=image_path,
                    user=user,
                    db=db
                )
                
                if post_result.get("success"):
                    post.status = PostStatus.POSTED
                    post.posted_at = datetime.utcnow()
                    post.platform_post_id = post_result.get("post_id", "")
                    results.append({
                        "platform": platform_str,
                        "success": True,
                        "message": post_result.get("message", "Posted successfully"),
                        "post_id": post.id
                    })
                else:
                    post.status = PostStatus.FAILED
                    post.last_error = post_result.get("error", "Unknown error")
                    results.append({
                        "platform": platform_str,
                        "success": False,
                        "message": post_result.get("error", "Failed to post"),
                        "post_id": post.id
                    })
                
                db.commit()
                
            except Exception as e:
                post.status = PostStatus.FAILED
                post.last_error = str(e)
                db.commit()
                results.append({
                    "platform": platform_str,
                    "success": False,
                    "message": str(e),
                    "post_id": post.id
                })
        else:
            results.append({
                "platform": platform_str,
                "success": True,
                "message": f"Scheduled for {scheduled_dt.isoformat()}",
                "post_id": post.id
            })
    
    # Determine overall success
    all_success = all(r["success"] for r in results)
    any_success = any(r["success"] for r in results)
    
    if all_success:
        message = "All posts created successfully!"
    elif any_success:
        message = "Some posts created successfully"
    else:
        message = "Failed to create posts"
    
    return ManualPostResponse(
        success=any_success,
        message=message,
        posts=results
    )


async def _post_to_platform(
    platform: Platform,
    content: str,
    image_path: Optional[str],
    user: User,
    db: Session
) -> dict:
    """Post content to a specific platform."""
    try:
        if platform == Platform.LINKEDIN:
            service = get_linkedin_service(user, db)
            if image_path:
                result = await service.post_with_image(content, image_path)
            else:
                result = await service.post_content(content)
            return result
        
        elif platform == Platform.INSTAGRAM:
            service = get_instagram_service(user, db)
            if image_path:
                result = await service.post_with_image(content, image_path)
            else:
                result = await service.post_content(content)
            return result
        
        elif platform == Platform.FACEBOOK:
            service = get_facebook_service(user, db)
            if image_path:
                result = await service.post_with_image(content, image_path)
            else:
                result = await service.post_content(content)
            return result
        
        return {"success": False, "error": f"Unknown platform: {platform}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
