from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .routers import alerts, auth, bots, emergency, market, portfolio, signals, trades
from .services.ws_price_stream import get_price_stream_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup - start price stream service
    price_stream = get_price_stream_service()
    await price_stream.start()
    yield
    # shutdown - stop price stream service
    await price_stream.stop()


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
    app.include_router(bots.router)
    app.include_router(trades.router)
    app.include_router(emergency.router)

    @app.websocket("/ws/prices")
    async def websocket_prices(websocket: WebSocket):
        """WebSocket endpoint for real-time price updates."""
        price_stream = get_price_stream_service()
        await price_stream.add_client(websocket)
        
        try:
            # Keep connection alive - receive loop
            while True:
                # Client can send pings to keep alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            await price_stream.remove_client(websocket)

    return app


app = create_app()
