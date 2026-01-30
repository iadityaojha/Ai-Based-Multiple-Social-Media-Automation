"""
Database Configuration Module
=============================
Sets up SQLAlchemy with SQLite for the MVP.
Provides session management and base model class.

Easy to upgrade to PostgreSQL or other databases by changing DATABASE_URL.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.config import settings

# =========================================
# Database Engine Setup
# =========================================
# For SQLite, we need to add connect_args to allow multi-threading
# Remove this for PostgreSQL/MySQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# =========================================
# Session Factory
# =========================================
# SessionLocal is a factory for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,  # We want explicit commits
    autoflush=False,   # We want explicit flushes
    bind=engine
)

# =========================================
# Base Model Class
# =========================================
# All ORM models will inherit from this base
Base = declarative_base()


# =========================================
# Dependency Injection for FastAPI
# =========================================
def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after the request is complete.
    
    Usage in FastAPI routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions outside of FastAPI routes.
    Useful for background tasks and schedulers.
    
    Usage:
        with get_db_context() as db:
            posts = db.query(Post).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Should be called once at application startup.
    """
    # Import all models to ensure they're registered with Base
    from app import models  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
