import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqlalchemy import select

from app.core.config import settings
from app.infra.database import db_helper, Base
import app.domain.models as models
from app.probes.icmp_probe import run_icmp_probe
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in db_helper.session_getter():
        res = await session.execute(select(models.Device))
        if not res.scalars().first():
            session.add(models.Device(hostname="Google_DNS", ip_address="8.8.8.8", device_type="Router"))
            await session.commit()
            print("Додано тестовий пристрій Google_DNS.")

    probe_task = asyncio.create_task(run_icmp_probe())

    yield

    probe_task.cancel()
    await db_helper.dispose()


main_app = FastAPI(
    title=settings.project_name,
    debug=True,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


main_app.include_router(api_router)

@main_app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.project_name}


if __name__ == "__main__":
    uvicorn.run("main:main_app", reload=True, host=settings.run.host, port=settings.run.port)
