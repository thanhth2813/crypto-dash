from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..schemas.alert import AlertCreate, AlertResponse
from ..services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse)
async def create_alert(
    req: AlertCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> AlertResponse:
    a = await AlertService.create_alert(db, user.id, req)
    return AlertResponse(
        id=a.id,
        symbol=a.symbol,
        coin_id=a.coin_id,
        condition=a.condition,
        target_price=float(a.target_price),
        status=a.status,
        trigger_count=a.trigger_count,
        triggered_at=a.triggered_at,
    )


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> list[AlertResponse]:
    alerts = await AlertService.list_alerts(db, user.id)
    return [
        AlertResponse(
            id=a.id,
            symbol=a.symbol,
            coin_id=a.coin_id,
            condition=a.condition,
            target_price=float(a.target_price),
            status=a.status,
            trigger_count=a.trigger_count,
            triggered_at=a.triggered_at,
        )
        for a in alerts
    ]


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
) -> dict:
    await AlertService.delete_alert(db, user.id, alert_id)
    return {"ok": True}
