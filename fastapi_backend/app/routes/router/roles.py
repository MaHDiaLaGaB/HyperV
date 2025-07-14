from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.alert import AlertRead
from app.services.alert import AlertService
from app.services.deps import get_alert_service
from app.security.auth import current_active_user
from app.models.users.users import User

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get(
    "/unacknowledged",
    response_model=List[AlertRead],
    summary="List all unacknowledged alerts for organization",
)
async def list_unacknowledged_alerts(
    service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(current_active_user),
) -> List[AlertRead]:
    return await service.list_unack(current_user.organization_id)


@router.post(
    "/{alert_id}/acknowledge",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: int,
    service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(current_active_user),
) -> None:
    await service.acknowledge(current_user.organization_id, alert_id)
