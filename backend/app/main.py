from __future__ import annotations

from fastapi import FastAPI

from .routers import alerts, auth, market, portfolio, signals


def create_app() -> FastAPI:
    app = FastAPI(title="crypto-dash-backend")

    @app.on_event("startup")
    async def _startup() -> None:
        # Placeholder for DB/Redis init
        return None

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        return None

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
