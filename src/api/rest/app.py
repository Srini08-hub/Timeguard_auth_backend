from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.middleware.cors import setup_cors
from src.api.rest.routes.auth_routes import router as auth_router
from src.api.rest.routes.health_routes import router as health_router
from src.api.rest.routes.user_routes import router as user_router
from src.core.exceptions import handlers as exception_handlers
from src.data.clients.postgress_client import dispose_async_engine, init_async_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_async_engine()
    yield
    await dispose_async_engine()


def get_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    # register all app-specific exception handlers centrally
    setup_cors(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    exception_handlers.register_exception_handlers(app)
    return app
