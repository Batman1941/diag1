import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.api.routes import _purge_expired_sessions
from app.core.config import get_settings
from app.db.session import SessionLocal

settings = get_settings()
logger = logging.getLogger(__name__)


async def _cleanup_loop() -> None:
    while True:
        db = SessionLocal()
        try:
            _purge_expired_sessions(db)
        except Exception as exc:  # pragma: no cover - background safety path
            logger.warning("Background session cleanup failed: %s", exc)
        finally:
            db.close()
        await asyncio.sleep(900)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

app.include_router(router)
