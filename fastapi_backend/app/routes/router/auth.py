# app/routes/router/auth.py
from fastapi import APIRouter, Depends
from app.security.current_user import get_current_user, role_required
from app.schemas.users import CurrentUser

router = APIRouter()

# Exported aliases (handy for tests to override)
get_current_user = _get_current_user
admin_required = _role_required("admin")

@router.get("/me")
async def me(current: CurrentUser = Depends(get_current_user)):
    return current

@router.get("/check-admin")
async def check_admin(current: CurrentUser = Depends(admin_required)):
    return {"ok": True, "user_id": current["id"], "roles": current["roles"]}
