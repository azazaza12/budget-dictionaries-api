"""Composition root: сборка приложения. Запуск: uv run uvicorn sigma.main:app"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sigma.shared.db import engine
from sigma.shared.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="sigma", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Роутеры модулей: app.include_router(...) — здесь
    return app


app = create_app()
