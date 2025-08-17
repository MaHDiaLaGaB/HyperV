from fastapi import APIRouter
from fastapi import APIRouter, Depends
from app.security.clerk import get_current_user, role_required, CurrentUser

router = APIRouter()

# Simple "who am I" endpoint (replaces /auth/jwt/*, /auth/register, etc.)
@router.get("/auth/me", tags=["auth"])
async def me(current: CurrentUser = Depends(get_current_user)):
    return current

# Example: protect by org role (or superadmin via env SUPERADMINS)
@router.get("/auth/check-admin", tags=["auth"])
async def check_admin(current: CurrentUser = Depends(role_required("admin"))):
    return {"ok": True, "user_id": current["id"], "org_role": current["org_role"]}
