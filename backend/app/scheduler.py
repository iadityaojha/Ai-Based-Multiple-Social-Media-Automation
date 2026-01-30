"""
Background Scheduler for Auto-Posting
======================================
Checks for pending posts and publishes them automatically.
"""

import asyncio
from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db_context
from app.models import GeneratedPost, PostStatus, Platform, ErrorLog, User
from app.services.linkedin_service import get_linkedin_service
from app.services.instagram_service import get_instagram_service
from app.services.facebook_service import get_facebook_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostScheduler:
    """Background scheduler for automatic post publishing."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.max_retries = settings.MAX_RETRY_ATTEMPTS
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            return
        
        self.scheduler.add_job(
            self._check_pending_posts,
            trigger=IntervalTrigger(seconds=settings.SCHEDULER_CHECK_INTERVAL),
            id="check_pending",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"✓ Scheduler started (interval: {settings.SCHEDULER_CHECK_INTERVAL}s)")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("✓ Scheduler stopped")
    
    def _check_pending_posts(self):
        """Check and publish pending posts."""
        with get_db_context() as db:
            now = datetime.utcnow()
            pending = db.query(GeneratedPost).filter(
                GeneratedPost.status == PostStatus.PENDING,
                (GeneratedPost.scheduled_time == None) | (GeneratedPost.scheduled_time <= now)
            ).all()
            
            for post in pending:
                self._publish_post(db, post)
    
    def _publish_post(self, db: Session, post: GeneratedPost):
        """Publish a single post."""
        logger.info(f"Publishing post {post.id} to {post.platform.value}...")
        
        try:
            # Get user for this post
            user = db.query(User).filter(User.id == post.user_id).first()
            if not user:
                raise Exception("User not found")
            
            result = asyncio.run(self._post_to_platform(post, user, db))
            
            if result.get("success"):
                post.status = PostStatus.POSTED
                post.posted_at = datetime.utcnow()
                post.platform_post_id = result.get("post_id")
                logger.info(f"✓ Post {post.id} published")
            else:
                self._handle_failure(db, post, result.get("message", "Unknown error"))
                
        except Exception as e:
            self._handle_failure(db, post, str(e))
        
        db.commit()
    
    async def _post_to_platform(self, post: GeneratedPost, user: User, db: Session) -> dict:
        """Post to the appropriate platform."""
        hashtags = post.hashtags.split(",") if post.hashtags else None
        
        if post.platform == Platform.LINKEDIN:
            service = get_linkedin_service(user, db)
            return await service.post_content(post.content)
        
        elif post.platform == Platform.INSTAGRAM:
            service = get_instagram_service(user, db)
            return await service.post_content(post.content, hashtags=hashtags)
        
        elif post.platform == Platform.FACEBOOK:
            service = get_facebook_service(user, db)
            return await service.post_content(post.content)
        
        return {"success": False, "message": "Unsupported platform"}
    
    def _handle_failure(self, db: Session, post: GeneratedPost, error: str):
        """Handle posting failure with retry logic."""
        post.retry_count += 1
        post.last_error = error
        
        # Log error
        log = ErrorLog(
            post_id=post.id,
            error_message=error,
            attempt_number=post.retry_count
        )
        db.add(log)
        
        if post.retry_count >= self.max_retries:
            post.status = PostStatus.FAILED
            logger.error(f"✗ Post {post.id} failed after {post.retry_count} attempts")
        else:
            # Exponential backoff
            delay = 2 ** (post.retry_count - 1)
            post.scheduled_time = datetime.utcnow() + timedelta(minutes=delay)
            logger.warning(f"Post {post.id} will retry in {delay} min")


# Singleton
post_scheduler = PostScheduler()
