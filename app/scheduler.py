"""
Scheduler Module
================
Background task scheduler for automatic post publishing.

Features:
- Checks for pending posts at regular intervals
- Executes posting at scheduled times
- Retry logic with exponential backoff
- Error logging for failed posts

Uses APScheduler for background job management.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db_context
from app.models import GeneratedPost, PostStatus, Platform, ErrorLog
from app.services.linkedin_service import linkedin_service, LinkedInError
from app.services.instagram_service import instagram_service, InstagramError
from app.services.facebook_service import facebook_service, FacebookError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostScheduler:
    """
    Manages scheduled post publishing.
    
    The scheduler runs as a background process and:
    1. Periodically checks for posts that are ready to publish
    2. Attempts to post to the appropriate platform
    3. Retries failed posts with exponential backoff
    4. Logs errors for debugging
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.max_retries = settings.MAX_RETRY_ATTEMPTS
        self.check_interval = settings.SCHEDULER_CHECK_INTERVAL
    
    def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Add job to check for pending posts
        self.scheduler.add_job(
            self._check_pending_posts,
            trigger=IntervalTrigger(seconds=self.check_interval),
            id="check_pending_posts",
            name="Check and publish pending posts",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info(f"✓ Scheduler started (checking every {self.check_interval} seconds)")
    
    def stop(self):
        """Stop the background scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("✓ Scheduler stopped")
    
    def _check_pending_posts(self):
        """
        Check for posts that are ready to be published.
        This is called periodically by the scheduler.
        """
        logger.info("Checking for pending posts...")
        
        with get_db_context() as db:
            # Find all pending posts that are ready to publish
            now = datetime.utcnow()
            pending_posts = db.query(GeneratedPost).filter(
                GeneratedPost.status == PostStatus.PENDING,
                # Either no scheduled time (post immediately) or scheduled time has passed
                (GeneratedPost.scheduled_time == None) | (GeneratedPost.scheduled_time <= now)
            ).all()
            
            if not pending_posts:
                logger.info("No pending posts to publish")
                return
            
            logger.info(f"Found {len(pending_posts)} posts to publish")
            
            for post in pending_posts:
                self._publish_post(db, post)
    
    def _publish_post(self, db: Session, post: GeneratedPost):
        """
        Attempt to publish a single post.
        
        Args:
            db: Database session
            post: The post to publish
        """
        logger.info(f"Publishing post {post.id} to {post.platform.value}...")
        
        try:
            # Run the async posting function synchronously
            result = asyncio.run(self._post_to_platform(post))
            
            if result.get("success"):
                # Update post status to posted
                post.status = PostStatus.POSTED
                post.posted_at = datetime.utcnow()
                post.platform_post_id = result.get("post_id")
                db.commit()
                
                logger.info(f"✓ Post {post.id} published successfully to {post.platform.value}")
            else:
                # Handle failure
                self._handle_failure(db, post, result.get("message", "Unknown error"))
                
        except Exception as e:
            self._handle_failure(db, post, str(e))
    
    async def _post_to_platform(self, post: GeneratedPost) -> dict:
        """
        Post content to the appropriate platform.
        
        Args:
            post: The post to publish
            
        Returns:
            Dict with success status and details
        """
        content = post.content
        hashtags = post.hashtags.split(",") if post.hashtags else None
        
        if post.platform == Platform.LINKEDIN:
            return await linkedin_service.post_content(content)
        
        elif post.platform == Platform.INSTAGRAM:
            return await instagram_service.post_content(content, hashtags=hashtags)
        
        elif post.platform == Platform.FACEBOOK:
            return await facebook_service.post_content(content)
        
        else:
            return {
                "success": False,
                "message": f"Unsupported platform: {post.platform}"
            }
    
    def _handle_failure(self, db: Session, post: GeneratedPost, error_message: str):
        """
        Handle a failed posting attempt.
        
        Implements retry logic with exponential backoff.
        
        Args:
            db: Database session
            post: The post that failed
            error_message: Description of the error
        """
        post.retry_count += 1
        
        # Log the error
        error_log = ErrorLog(
            post_id=post.id,
            error_message=error_message,
            error_type=type(error_message).__name__,
            attempt_number=post.retry_count
        )
        db.add(error_log)
        
        if post.retry_count >= self.max_retries:
            # Max retries exceeded - mark as failed
            post.status = PostStatus.FAILED
            logger.error(f"✗ Post {post.id} failed after {post.retry_count} attempts: {error_message}")
        else:
            # Schedule retry with exponential backoff
            # Retry delays: 1min, 2min, 4min, 8min, etc.
            delay_minutes = 2 ** (post.retry_count - 1)
            post.scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
            logger.warning(
                f"Post {post.id} failed (attempt {post.retry_count}/{self.max_retries}). "
                f"Retrying in {delay_minutes} minute(s). Error: {error_message}"
            )
        
        db.commit()
    
    def schedule_post(self, post_id: int, scheduled_time: Optional[datetime] = None):
        """
        Schedule a post for publishing.
        
        Args:
            post_id: ID of the post to schedule
            scheduled_time: When to publish (None = immediately)
        """
        with get_db_context() as db:
            post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
            
            if not post:
                raise ValueError(f"Post {post_id} not found")
            
            post.status = PostStatus.PENDING
            post.scheduled_time = scheduled_time
            db.commit()
            
            if scheduled_time:
                logger.info(f"Post {post_id} scheduled for {scheduled_time}")
            else:
                logger.info(f"Post {post_id} queued for immediate publishing")
    
    def cancel_post(self, post_id: int):
        """
        Cancel a scheduled post.
        
        Args:
            post_id: ID of the post to cancel
        """
        with get_db_context() as db:
            post = db.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
            
            if not post:
                raise ValueError(f"Post {post_id} not found")
            
            if post.status == PostStatus.POSTED:
                raise ValueError("Cannot cancel a post that has already been published")
            
            post.status = PostStatus.DRAFT
            post.scheduled_time = None
            db.commit()
            
            logger.info(f"Post {post_id} cancelled")
    
    def get_pending_count(self) -> int:
        """Get the count of pending posts."""
        with get_db_context() as db:
            return db.query(GeneratedPost).filter(
                GeneratedPost.status == PostStatus.PENDING
            ).count()


# Create singleton scheduler instance
post_scheduler = PostScheduler()
