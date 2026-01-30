"""
AI Social Media Automation Platform - Main Application
======================================================
FastAPI application entry point.

This module:
- Initializes the FastAPI application
- Configures middleware and templates
- Registers API routes
- Starts the background scheduler on startup
- Serves the frontend dashboard
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.database import init_db
from app.routes import generate_router, schedule_router, keys_router
from app.scheduler import post_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =========================================
# Application Lifespan (Startup/Shutdown)
# =========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    On startup:
    - Initialize database tables
    - Validate configuration
    - Start the background scheduler
    
    On shutdown:
    - Stop the scheduler gracefully
    """
    # Startup
    logger.info("=" * 50)
    logger.info("AI Social Media Automation Platform Starting...")
    logger.info("=" * 50)
    
    # Validate settings
    errors = settings.validate()
    if errors:
        for error in errors:
            logger.warning(f"Configuration warning: {error}")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Start scheduler
    try:
        post_scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        # Non-fatal - app can still work without scheduler
    
    logger.info("✓ Application started successfully")
    logger.info(f"  - API docs: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/docs")
    logger.info(f"  - Dashboard: http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/")
    logger.info("=" * 50)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    post_scheduler.stop()
    logger.info("✓ Application stopped")


# =========================================
# Create FastAPI Application
# =========================================
app = FastAPI(
    title="AI Social Media Automation Platform",
    description="""
    An AI-powered platform for generating and scheduling social media content
    focused on AI education.
    
    ## Features
    
    * **Content Generation**: Generate platform-specific content using LLM
    * **Multi-Platform Support**: LinkedIn, Instagram, and Facebook
    * **Scheduling**: Schedule posts for automatic publishing
    * **Dashboard**: Simple web interface for content management
    
    ## API Endpoints
    
    * `/api/generate` - Generate content for a topic
    * `/api/topics` - Manage topics
    * `/api/posts` - Manage and schedule posts
    * `/api/stats` - Get posting statistics
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# =========================================
# Middleware Configuration
# =========================================
# CORS - Allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# Static Files and Templates
# =========================================
# Templates for the dashboard
templates = Jinja2Templates(directory="app/templates")


# =========================================
# Include API Routes
# =========================================
app.include_router(generate_router)
app.include_router(schedule_router)
app.include_router(keys_router)


# =========================================
# Frontend Routes
# =========================================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve the main dashboard page.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "AI Social Media Automation",
            "debug": settings.DEBUG
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "scheduler_running": post_scheduler.is_running,
        "pending_posts": post_scheduler.get_pending_count()
    }


# =========================================
# Error Handlers
# =========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
    }


# =========================================
# Run with Uvicorn (for development)
# =========================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG
    )
