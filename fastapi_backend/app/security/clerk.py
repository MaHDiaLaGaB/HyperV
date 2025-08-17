# app/security/clerk_auth.py
import os, time
from functools import lru_cache
from typing import Any, Dict, List, Optional, TypedDict
from jose import jwt

import httpx
from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db
from app.models.users.users import User
from app.models.users.organization import Organization

# ---- Settings (env) ----
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "")  # e.g. https://your-domain.clerk.accounts.dev
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", f"{CLERK_ISSUER}/.well-known/jwks.json")
CLERK_PERMITTED_AZP = {s.strip() for s in os.getenv("CLERK_PERMITTED_AZP", "").split(",") if s.strip()}
SUPERADMINS = {s.strip() for s in os.getenv("SUPERADMINS", "").split(",") if s.strip()}  # clerk user ids

ALGORITHMS = ["RS256"]
bearer = HTTPBearer(auto_error=True)

class AuthContext(TypedDict, total=False):
    # raw claims (Clerk v2)
    sub: str
    org_id: Optional[str]
    org_role: Optional[str]
    org_slug: Optional[str]
    org_permissions: List[str]
    azp: Optional[str]

@lru_cache(maxsize=1)
def _jwks() -> Dict[str, Any]:
    try:
        res = httpx.get(CLERK_JWKS_URL, timeout=5.0)
        res.raise_for_status()
        return res.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load Clerk JWKS")

def _public_key_for(token: str):
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    for key in _jwks()["keys"]:
        if key.get("kid") == kid:
            # jose accepts PEM key via from_jwk
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)
    raise HTTPException(status_code=401, detail="Unknown key id (kid)")

def _decode_clerk(token: str) -> Dict[str, Any]:
    key = _public_key_for(token)
    # Validate signature + issuer; Clerk tokens typically omit `aud`, so don't enforce it.
    claims = jwt.decode(
        token,
        key=key,
        algorithms=ALGORITHMS,
        issuer=CLERK_ISSUER,
        options={"verify_aud": False},
    )
    now = int(time.time())
    if int(claims.get("exp", 0)) < now or int(claims.get("nbf", 0)) > now:
        raise HTTPException(status_code=401, detail="Token expired or not yet valid")

    azp = claims.get("azp")
    if CLERK_PERMITTED_AZP and azp not in CLERK_PERMITTED_AZP:
        raise HTTPException(status_code=401, detail="Invalid 'azp' (origin)")

    return claims

def _claims_to_ctx(claims: Dict[str, Any]) -> AuthContext:
    # Support v2 claims directly
    ctx: AuthContext = {
        "sub": claims.get("sub"),
        "azp": claims.get("azp"),
        "org_id": claims.get("org_id") or (claims.get("o") or {}).get("id"),
        "org_role": claims.get("org_role") or (claims.get("o") or {}).get("rol"),
        "org_slug": claims.get("org_slug") or (claims.get("o") or {}).get("slg"),
        "org_permissions": claims.get("org_permissions") or (claims.get("o") or {}).get("per") or [],
    }
    if not ctx["sub"]:
        raise HTTPException(status_code=401, detail="Missing subject in token")
    return ctx

async def require_clerk_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> AuthContext:
    token = credentials.credentials
    claims = _decode_clerk(token)
    return _claims_to_ctx(claims)

# ---- Map Clerk -> your DB user + org ----

class CurrentUser(TypedDict):
    id: str                 # your local UUID (as str)
    clerk_user_id: str
    email: Optional[str]
    full_name: Optional[str]
    organization_id: Optional[str]
    org_role: Optional[str]
    org_slug: Optional[str]
    is_superadmin: bool
    permissions: List[str]

async def get_current_user(
    ctx: AuthContext = Depends(require_clerk_claims),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    clerk_id = ctx["sub"]

    # Try to find local user by clerk_user_id
    user = await db.scalar(select(User).where(User.clerk_user_id == clerk_id))
    if not user:
        # First-time “auto-provision”: create a minimal local user row.
        # If you want richer data, fetch from Clerk Backend API using CLERK_SECRET_KEY.
        user = User(clerk_user_id=clerk_id, full_name="", email=None)  # adapt fields to your model
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # If token has an active org, try to map to a local organization via organizations.clerk_org_id
    org_id = None
    if ctx.get("org_id"):
        org = await db.scalar(select(Organization).where(Organization.clerk_org_id == ctx["org_id"]))
        if org:
            org_id = str(org.id)
            # Optional: keep user.organization_id synced to active org
            user.organization_id = org.id
            await db.commit()

    return {
        "id": str(user.id),
        "clerk_user_id": clerk_id,
        "email": getattr(user, "email", None),
        "full_name": getattr(user, "full_name", None),
        "organization_id": org_id,
        "org_role": ctx.get("org_role"),
        "org_slug": ctx.get("org_slug"),
        "is_superadmin": clerk_id in SUPERADMINS,
        "permissions": list(ctx.get("org_permissions") or []),
    }

# ---- Role/permission guard compatible with your existing style ----
from fastapi import HTTPException

def role_required(*allowed_roles: str):
    allowed = set(allowed_roles)
    async def _dep(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current["is_superadmin"]:
            return current
        if current["org_role"] and (current["org_role"].split(":")[-1] in allowed):
            return current
        # Fallback: also allow via DB role assignments if you want:
        #   - check current user's Role names in your join tables here
        raise HTTPException(status_code=403, detail="Forbidden")
    return _dep

# ---- WebSocket variant (Authorization header or ?token=...) ----
async def get_current_user_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    auth = websocket.headers.get("authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        token = websocket.query_params.get("token") or ""
    if not token:
        await websocket.close(code=4401)
        raise HTTPException(status_code=401, detail="Missing token")

    claims = _decode_clerk(token)
    ctx = _claims_to_ctx(claims)
    # Reuse mapping to DB:
    return await get_current_user(ctx, db)
