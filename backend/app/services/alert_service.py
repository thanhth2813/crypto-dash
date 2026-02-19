from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.alert import Alert
from ..schemas.alert import AlertCreate


class AlertService:
    @staticmethod
    async def create_alert(db: AsyncSession, user_id: int, req: AlertCreate) -> Alert:
        # Minimal validation
        if req.condition not in ("above", "below"):
            raise HTTPException(status_code=422, detail="invalid condition")

        alert = Alert(
            user_id=user_id,
            coin_id=req.coin_id,
            symbol=req.symbol,
            condition=req.condition,
            target_price=req.target_price,
            status="active",
            trigger_count=0,
            triggered_at=None,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def list_alerts(db: AsyncSession, user_id: int) -> list[Alert]:
        res = await db.execute(select(Alert).where(Alert.user_id == user_id).order_by(Alert.id.desc()))
        return list(res.scalars().all())

    @staticmethod
    async def delete_alert(db: AsyncSession, user_id: int, alert_id: int) -> None:
        res = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id))
        alert = res.scalar_one_or_none()
        if alert is None:
            raise HTTPException(status_code=404, detail="alert not found")

        await db.delete(alert)
        await db.commit()
