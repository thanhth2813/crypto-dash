"""WebSocket price stream service.

Connects to Binance WebSocket API and broadcasts real-time prices
to connected frontend clients.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

import websockets
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class PriceStreamService:
    """Real-time price streaming from Binance to frontend clients."""

    def __init__(self):
        self.binance_ws_url = "wss://stream.binance.com:9443/ws"
        self.connected_clients: Set[WebSocket] = set()
        self.binance_ws = None
        self.running = False
        self._reconnect_delay = 5  # seconds
        self._heartbeat_interval = 30  # seconds

    async def connect_to_binance(self):
        """Connect to Binance WebSocket and subscribe to miniTicker for top 20 coins."""
        
        # Subscribe to combined stream for top coins
        # Format: BTCUSDT@miniTicker, ETHUSDT@miniTicker, etc.
        top_symbols = [
            "btcusdt", "ethusdt", "bnbusdt", "xrpusdt", "adausdt",
            "dogeusdt", "solusdt", "dotusdt", "maticusdt", "ltcusdt",
            "shibusdt", "trxusdt", "avaxusdt", "linkusdt", "uniusdt",
            "xlmusdt", "atomusdt", "etcusdt", "filusdt", "hbarusdt",
        ]
        
        streams = [f"{symbol}@miniTicker" for symbol in top_symbols]
        combined_stream = "/".join(streams)
        ws_url = f"{self.binance_ws_url}/{combined_stream}"
        
        try:
            logger.info(f"Connecting to Binance WebSocket: {ws_url[:100]}...")
            self.binance_ws = await websockets.connect(ws_url)
            logger.info("Connected to Binance WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            return False

    async def broadcast_to_clients(self, message: dict):
        """Broadcast price update to all connected frontend clients."""
        if not self.connected_clients:
            return
        
        # Remove disconnected clients
        disconnected = set()
        
        for client in self.connected_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(client)
        
        # Clean up disconnected clients
        self.connected_clients -= disconnected

    async def listen_binance_stream(self):
        """Listen to Binance WebSocket and broadcast to clients."""
        while self.running:
            try:
                if not self.binance_ws:
                    connected = await self.connect_to_binance()
                    if not connected:
                        await asyncio.sleep(self._reconnect_delay)
                        continue
                
                # Receive message from Binance
                raw_message = await asyncio.wait_for(
                    self.binance_ws.recv(),
                    timeout=self._heartbeat_interval + 10
                )
                
                data = json.loads(raw_message)
                
                # Parse miniTicker format
                # {
                #   "e": "24hrMiniTicker",
                #   "E": 1672515782136,
                #   "s": "BTCUSDT",
                #   "c": "16950.00",  # close price
                #   "o": "16800.00",  # open price
                #   "h": "17000.00",  # high
                #   "l": "16750.00",  # low
                #   "v": "1000.00",   # volume
                #   "q": "16900000.00" # quote volume
                # }
                
                if data.get("e") == "24hrMiniTicker":
                    price_update = {
                        "type": "price_update",
                        "symbol": data.get("s"),
                        "price": float(data.get("c", 0)),
                        "open": float(data.get("o", 0)),
                        "high": float(data.get("h", 0)),
                        "low": float(data.get("l", 0)),
                        "volume": float(data.get("v", 0)),
                        "timestamp": data.get("E"),
                    }
                    
                    # Broadcast to all connected clients
                    await self.broadcast_to_clients(price_update)
            
            except asyncio.TimeoutError:
                logger.warning("Binance WebSocket timeout - sending heartbeat")
                try:
                    # Send ping to keep connection alive
                    await self.binance_ws.ping()
                except Exception as e:
                    logger.error(f"Heartbeat failed: {e}")
                    self.binance_ws = None
            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Binance WebSocket connection closed - reconnecting")
                self.binance_ws = None
                await asyncio.sleep(self._reconnect_delay)
            
            except Exception as e:
                logger.error(f"Error in Binance stream: {e}", exc_info=True)
                self.binance_ws = None
                await asyncio.sleep(self._reconnect_delay)

    async def add_client(self, websocket: WebSocket):
        """Add a new frontend client to receive price updates."""
        await websocket.accept()
        self.connected_clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to price stream",
            "symbols": 20,
        })

    async def remove_client(self, websocket: WebSocket):
        """Remove a frontend client."""
        self.connected_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def start(self):
        """Start the price stream service."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting price stream service")
        
        # Start listening to Binance in background
        asyncio.create_task(self.listen_binance_stream())

    async def stop(self):
        """Stop the price stream service."""
        self.running = False
        
        if self.binance_ws:
            await self.binance_ws.close()
        
        # Close all client connections
        for client in self.connected_clients:
            try:
                await client.close()
            except Exception:
                pass
        
        self.connected_clients.clear()
        logger.info("Price stream service stopped")


# Global singleton instance
_price_stream_service: PriceStreamService | None = None


def get_price_stream_service() -> PriceStreamService:
    """Get or create singleton PriceStreamService instance."""
    global _price_stream_service
    if _price_stream_service is None:
        _price_stream_service = PriceStreamService()
    return _price_stream_service
