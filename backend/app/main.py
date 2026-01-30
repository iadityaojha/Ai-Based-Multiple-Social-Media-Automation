"""
FastAPI Main Application
========================
SaaS web application for AI-powered social media automation.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import auth_router, api_keys_router, generate_router, schedule_router, manual_post_router
from app.scheduler import post_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    logger.info("=" * 50)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting...")
    
    # Validate config
    errors = settings.validate()
    for e in errors:
        logger.warning(f"Config warning: {e}")
    
    # Init database
    init_db()
    
    # Start scheduler
    post_scheduler.start()
    
    logger.info(f"✓ Server ready at http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info(f"✓ API docs at http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/docs")
    logger.info("=" * 50)
    
    yield
    
    post_scheduler.stop()
    logger.info("✓ Application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered social media content generation and scheduling platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(generate_router)
app.include_router(schedule_router)
app.include_router(manual_post_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "scheduler": post_scheduler.is_running
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=settings.DEBUG)
