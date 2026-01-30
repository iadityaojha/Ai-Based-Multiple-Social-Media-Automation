"""Routes package init."""

from app.routes.auth import router as auth_router
from app.routes.api_keys import router as api_keys_router
from app.routes.generate import router as generate_router
from app.routes.schedule import router as schedule_router
from app.routes.manual_post import router as manual_post_router

__all__ = ["auth_router", "api_keys_router", "generate_router", "schedule_router", "manual_post_router"]
