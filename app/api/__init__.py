from fastapi import APIRouter
from app.core.config import settings
from .v1 import router as v1_router

router = APIRouter(prefix=settings.api.api_prefix)

router.include_router(v1_router, prefix=settings.api.v1.prefix)