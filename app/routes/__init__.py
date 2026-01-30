"""
Init file for routes package
"""

from app.routes.generate import router as generate_router
from app.routes.schedule import router as schedule_router
from app.routes.keys import router as keys_router

__all__ = ["generate_router", "schedule_router", "keys_router"]
