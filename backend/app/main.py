from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import alerts, auth, market, portfolio, signals


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup (placeholder)
    yield
    # shutdown (placeholder)


def create_app() -> FastAPI:
    app = FastAPI(title="crypto-dash-backend", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(market.router)
    app.include_router(portfolio.router)
    app.include_router(alerts.router)
    app.include_router(signals.router)

    return app


app = create_app()
