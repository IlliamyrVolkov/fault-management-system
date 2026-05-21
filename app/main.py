import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api import router as api_router
from app.core.config import settings
from app.core.logger import logger
from app.infra.database import Base, db_helper
import app.domain.models  # noqa: F401  # registers ORM models with Base.metadata
from app.probes.icmp_probe import run_icmp_probe


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Схема БД готова, фонові задачі запускаються.")

    probe_task = asyncio.create_task(run_icmp_probe())

    try:
        yield
    finally:
        probe_task.cancel()
        try:
            await probe_task
        except asyncio.CancelledError:
            pass
        await db_helper.dispose()
        logger.info("Фонові задачі зупинено, з'єднання з БД закриті.")


main_app = FastAPI(
    title=settings.project_name,
    debug=True,
    lifespan=lifespan,
)

main_app.include_router(api_router)


@main_app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.project_name}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:main_app",
        reload=True,
        host=settings.run.host,
        port=settings.run.port,
    )
