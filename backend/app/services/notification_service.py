"""Notification service - Telegram alerts for bot events."""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """Send Telegram notifications for trading events."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning("Telegram notifications disabled - TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")

    async def send_message(self, text: str) -> bool:
        """Send a Telegram message.
        
        Returns True if sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.debug(f"Telegram disabled - would send: {text}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    logger.info(f"Telegram message sent: {text[:50]}...")
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}", exc_info=True)
            return False

    async def notify_trade_executed(
        self,
        bot_name: str,
        side: str,
        amount: float,
        symbol: str,
        price: float,
        pnl: Optional[float] = None,
    ) -> bool:
        """Send notification when a bot executes a trade."""
        
        # Format message
        side_emoji = "🟢" if side.upper() == "BUY" else "🔴"
        
        message = f"{side_emoji} <b>Bot Trade Executed</b>\n\n"
        message += f"🤖 Bot: {bot_name}\n"
        message += f"📊 {side.upper()} {amount:.8f} {symbol.replace('USDT', '')}\n"
        message += f"💰 Price: ${price:,.2f}\n"
        
        if pnl is not None:
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            pnl_sign = "+" if pnl >= 0 else ""
            message += f"{pnl_emoji} P&L: {pnl_sign}${pnl:.2f}\n"
        
        return await self.send_message(message)

    async def notify_circuit_breaker(
        self,
        reason: str,
        details: str,
    ) -> bool:
        """Send notification when circuit breaker is triggered."""
        
        message = "⚠️ <b>CIRCUIT BREAKER TRIGGERED</b>\n\n"
        message += f"Reason: {reason}\n"
        message += f"Details: {details}\n"
        message += "\n🛑 All bots have been stopped for safety."
        
        return await self.send_message(message)

    async def notify_alert_triggered(
        self,
        alert_name: str,
        condition: str,
        symbol: str,
        price: float,
    ) -> bool:
        """Send notification when a price alert is triggered."""
        
        message = "🔔 <b>Alert Triggered</b>\n\n"
        message += f"📌 {alert_name}\n"
        message += f"📊 {symbol}: ${price:,.2f}\n"
        message += f"Condition: {condition}\n"
        
        return await self.send_message(message)

    async def notify_bot_error(
        self,
        bot_name: str,
        error: str,
    ) -> bool:
        """Send notification when a bot encounters an error."""
        
        message = "❌ <b>Bot Error</b>\n\n"
        message += f"🤖 Bot: {bot_name}\n"
        message += f"Error: {error}\n"
        message += "\n⚠️ Bot has been stopped."
        
        return await self.send_message(message)

    async def notify_system_status(
        self,
        running_bots: int,
        total_exposure: float,
        error_bots: int,
    ) -> bool:
        """Send system status notification."""
        
        message = "ℹ️ <b>System Status</b>\n\n"
        message += f"🤖 Running bots: {running_bots}\n"
        message += f"💰 Total exposure: ${total_exposure:,.2f}\n"
        
        if error_bots > 0:
            message += f"❌ Error bots: {error_bots}\n"
        
        return await self.send_message(message)


# Global singleton instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create singleton NotificationService instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
