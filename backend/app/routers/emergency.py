"""Emergency API endpoints - system-wide controls."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..models.user import User
from ..services.emergency_service import EmergencyService

router = APIRouter(prefix="/emergency", tags=["emergency"])


class StopAllRequest(BaseModel):
    reason: str = "Emergency stop requested by user"


class ForceStopRequest(BaseModel):
    reason: str = "Force stop requested by user"


@router.post("/stop-all")
async def stop_all_bots(
    request: StopAllRequest,
    current_user: User = Depends(get_current_user),
):
    """Stop ALL running bots immediately.
    
    CRITICAL: Use only in emergencies.
    This will stop all bots regardless of their state.
    """
    results = await EmergencyService.stop_all_bots(reason=request.reason)
    
    return {
        "message": "Emergency stop executed",
        "stopped_count": len(results["stopped"]),
        "failed_count": len(results["failed"]),
        "total_bots": results["total"],
        "stopped": results["stopped"],
        "failed": results["failed"],
    }


@router.post("/stop/{bot_id}")
async def force_stop_bot(
    bot_id: int,
    request: ForceStopRequest,
    current_user: User = Depends(get_current_user),
):
    """Force stop a specific bot.
    
    Works even if bot is in error state.
    """
    result = await EmergencyService.force_stop_bot(bot_id, reason=request.reason)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Stop failed"))
    
    return {
        "message": "Bot stopped",
        "bot_id": result["bot_id"],
        "name": result["name"],
        "reason": result["reason"],
    }


@router.get("/status")
async def get_emergency_status(
    current_user: User = Depends(get_current_user),
):
    """Get system health status.
    
    Returns:
    - Running bots count
    - Total exposure (invested capital)
    - Circuit breakers status
    - Error bots count
    - Status breakdown
    """
    status = await EmergencyService.get_system_status()
    
    return {
        "running_bots": status["running_bots"],
        "error_bots": status["error_bots"],
        "total_exposure": status["total_exposure"],
        "scheduler_active": status["scheduler_active"],
        "status_breakdown": status["status_breakdown"],
        "circuit_breakers": status["circuit_breakers"],
        "running_bot_details": status["running_bot_details"],
    }
