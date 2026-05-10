import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.infra.database import db_helper, Base
# from api import router as api_router
import app.domain.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await db_helper.dispose()


main_app = FastAPI(
    title=settings.project_name,
    debug=True,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


# main_app.include_router(api_router)

@main_app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.project_name}


if __name__ == "__main__":
    uvicorn.run("main:main_app", reload=True, host=settings.run.host, port=settings.run.port)
