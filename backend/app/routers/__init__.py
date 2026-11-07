from app.routers.admin import router as admin_router
from app.routers.cafe import router as cafe_router
from app.routers.dean import router as dean_router
from app.routers.printing import router as printing_router
from app.routers.queues import router as queues_router
from app.routers.tokens import router as tokens_router

__all__ = [
    "admin_router",
    "cafe_router",
    "dean_router",
    "printing_router",
    "queues_router",
    "tokens_router",
]
