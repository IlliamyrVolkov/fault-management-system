from fastapi import APIRouter
from app.core.config import settings
from .dashboard import router as dashboard_router

router = APIRouter()

router.include_router(
    dashboard_router,
    prefix=settings.api.v1.dashboard
)
