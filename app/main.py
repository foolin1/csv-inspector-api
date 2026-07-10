from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.files import router as files_router
from app.config import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    STORAGE_DIR,
)


def create_application() -> FastAPI:
    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    register_exception_handlers(application)
    application.include_router(files_router)

    @application.get(
        "/",
        include_in_schema=False,
    )
    async def root() -> dict[str, str]:
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "docs": "/docs",
        }

    @application.get(
        "/health",
        tags=["System"],
        summary="Check API health",
    )
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_application()
