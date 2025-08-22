# app/security/clerk_auth.py
import httpx
from typing import Any, Dict, Optional, TypedDict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHMS = ["RS256"]
bearer = HTTPBearer(auto_error=True)

class ClerkClaims(TypedDict, total=False):
    iss: str
    sub: str
    iat: int
    exp: int
    nbf: int
    azp: str
    aud: Any
    sid: str
    # Optional extras if you add a JWT template later:
    email: str
    name: str

async def _fetch_jwks() -> Dict[str, Any]:
    if not settings.CLERK_JWKS_URL:
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL not configured")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.CLERK_JWKS_URL)
        resp.raise_for_status()
        return resp.json()

def _find_key(jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            return k
    return None

async def verify_clerk_session_token(token: str) -> ClerkClaims:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Missing kid")

        jwks = await _fetch_jwks()
        key = _find_key(jwks, kid)
        if not key:
            raise HTTPException(status_code=401, detail="Unknown signing key")

        claims: ClerkClaims = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            issuer=settings.CLERK_ISSUER or None,
            options={"verify_aud": False},
        )

        # Optional: restrict to your frontend app(s)
        if settings.CLERK_ALLOWED_AZP_SET:
            azp = claims.get("azp")
            if not azp or azp not in settings.CLERK_ALLOWED_AZP_SET:
                raise HTTPException(status_code=401, detail="Invalid authorized party")

        if not claims.get("sub"):
            raise HTTPException(status_code=401, detail="Missing sub in token")

        return claims
    except HTTPException:
        raise
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def require_clerk_session(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> ClerkClaims:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return await verify_clerk_session_token(creds.credentials)
