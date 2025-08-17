from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path, status

from app.schemas.alert import AlertRead
from app.services.deps import get_alert_service
from app.services.alert import AlertService
from app.security.clerk import get_current_user, CurrentUser

router = APIRouter()


@router.get(
    "/unacknowledged",
    response_model=List[AlertRead],
    summary="List unacknowledged alerts",
)
async def list_unacknowledged_alerts(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> List[AlertRead]:
    """Retrieve unacknowledged alerts for the caller's scope (org/user)."""
    return await service.list_unack(current, limit=limit, offset=offset)


@router.post(
    "/{alert_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: UUID = Path(..., description="ID of the alert to acknowledge"),
    current: CurrentUser = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> None:
    """Mark an alert as acknowledged (scoped by org/user in service)."""
    await service.acknowledge(current, alert_id)
