import os
import pytest
import pytest_asyncio
import time
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select
from app.security.clerk import (
    _jwks, _public_key_for, _decode_clerk, _claims_to_ctx,
    require_clerk_claims, get_current_user, role_required,
    get_current_user_ws, AuthContext, CurrentUser
)
from app.models.users.users import User
from app.models.users.organization import Organization
from app.schemas.enums import ClientType


@pytest.fixture
def mock_jwt_header():
    return {"kid": "test-kid"}


@pytest.fixture
def mock_jwks():
    return {
        "keys": [
            {
                "kid": "test-kid",
                "kty": "RSA",
                "n": "test-n",
                "e": "AQAB"
            }
        ]
    }


@pytest.fixture
def mock_token():
    return "test-token"


@pytest.fixture
def mock_claims():
    return {
        "sub": "test-clerk-id",
        "azp": "test-azp",
        "exp": int(time.time()) + 3600,  # 1 hour from now
        "nbf": int(time.time()) - 60,   # 1 minute ago
        "org_id": "test-org-id",
        "org_role": "org:admin",
        "org_slug": "test-org",
        "org_permissions": ["read:users", "write:users"]
    }


@pytest.fixture
def mock_auth_context():
    return {
        "sub": "test-clerk-id",
        "azp": "test-azp",
        "org_id": "test-org-id",
        "org_role": "org:admin",
        "org_slug": "test-org",
        "org_permissions": ["read:users", "write:users"]
    }


class TestClerkAuth:
    @pytest.mark.asyncio
    async def test_jwks(self, monkeypatch):
        # Mock httpx.get
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": ["test-key"]}
        mock_response.raise_for_status.return_value = None
        
        with patch("httpx.get", return_value=mock_response):
            result = _jwks()
            assert result == {"keys": ["test-key"]}
    
    @pytest.mark.asyncio
    async def test_jwks_error(self, monkeypatch):
        # Mock httpx.get to raise an exception
        with patch("httpx.get", side_effect=Exception("Connection error")):
            with pytest.raises(HTTPException) as excinfo:
                _jwks()
            assert excinfo.value.status_code == 500
            assert excinfo.value.detail == "Failed to load Clerk JWKS"
    
    @pytest.mark.asyncio
    async def test_public_key_for(self, mock_token, mock_jwt_header, mock_jwks):
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("jose.jwt.get_unverified_header", return_value=mock_jwt_header), \
             patch("jose.jwt.algorithms.RSAAlgorithm.from_jwk", return_value="test-key"):
            result = _public_key_for(mock_token)
            assert result == "test-key"
    
    @pytest.mark.asyncio
    async def test_public_key_for_unknown_kid(self, mock_token, monkeypatch):
        with patch("jose.jwt.get_unverified_header", return_value={"kid": "unknown-kid"}), \
             patch("app.security.clerk._jwks", return_value={"keys": []}):
            with pytest.raises(HTTPException) as excinfo:
                _public_key_for(mock_token)
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Unknown key id (kid)"
    
    @pytest.mark.asyncio
    async def test_decode_clerk(self, mock_token, mock_claims):
        with patch("app.security.clerk._public_key_for", return_value="test-key"), \
             patch("jose.jwt.decode", return_value=mock_claims), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            result = _decode_clerk(mock_token)
            assert result == mock_claims
    
    @pytest.mark.asyncio
    async def test_decode_clerk_expired_token(self, mock_token):
        expired_claims = {
            "exp": int(time.time()) - 3600,  # 1 hour ago
            "nbf": int(time.time()) - 7200  # 2 hours ago
        }
        with patch("app.security.clerk._public_key_for", return_value="test-key"), \
             patch("jose.jwt.decode", return_value=expired_claims):
            with pytest.raises(HTTPException) as excinfo:
                _decode_clerk(mock_token)
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Token expired or not yet valid"
    
    @pytest.mark.asyncio
    async def test_decode_clerk_future_token(self, mock_token):
        future_claims = {
            "exp": int(time.time()) + 7200,  # 2 hours from now
            "nbf": int(time.time()) + 3600  # 1 hour from now
        }
        with patch("app.security.clerk._public_key_for", return_value="test-key"), \
             patch("jose.jwt.decode", return_value=future_claims):
            with pytest.raises(HTTPException) as excinfo:
                _decode_clerk(mock_token)
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Token expired or not yet valid"
    
    @pytest.mark.asyncio
    async def test_decode_clerk_invalid_azp(self, mock_token, mock_claims):
        with patch("app.security.clerk._public_key_for", return_value="test-key"), \
             patch("jose.jwt.decode", return_value=mock_claims), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", {"allowed-azp"}):
            with pytest.raises(HTTPException) as excinfo:
                _decode_clerk(mock_token)
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Invalid 'azp' (origin)"
    
    @pytest.mark.asyncio
    async def test_claims_to_ctx(self, mock_claims):
        result = _claims_to_ctx(mock_claims)
        assert result["sub"] == mock_claims["sub"]
        assert result["azp"] == mock_claims["azp"]
        assert result["org_id"] == mock_claims["org_id"]
        assert result["org_role"] == mock_claims["org_role"]
        assert result["org_slug"] == mock_claims["org_slug"]
        assert result["org_permissions"] == mock_claims["org_permissions"]
    
    @pytest.mark.asyncio
    async def test_claims_to_ctx_missing_subject(self):
        with pytest.raises(HTTPException) as excinfo:
            _claims_to_ctx({"azp": "test-azp"})
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Missing subject in token"
    
    @pytest.mark.asyncio
    async def test_require_clerk_claims(self):
        mock_credentials = MagicMock()
        mock_credentials.credentials = "test-token"
        mock_ctx = {"sub": "test-clerk-id"}
        
        with patch("app.security.clerk._decode_clerk", return_value={}), \
             patch("app.security.clerk._claims_to_ctx", return_value=mock_ctx):
            result = await require_clerk_claims(mock_credentials)
            assert result == mock_ctx


@pytest.mark.asyncio
class TestClerkUserIntegration:
    async def test_get_current_user_existing(self, db_session, mock_auth_context):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a test organization
        org = Organization(
            name="Test Org",
            slug="test-org",
            clerk_org_id="test-org-id",
            client_type=ClientType.ENTERPRISE,
            is_active=True
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        # Test get_current_user
        with patch("app.security.clerk.SUPERADMINS", {"other-clerk-id"}):
            result = await get_current_user(mock_auth_context, db_session)
            
            assert result["id"] == str(user.id)
            assert result["clerk_user_id"] == "test-clerk-id"
            assert result["email"] == "test@example.com"
            assert result["full_name"] == "Test User"
            assert result["organization_id"] == str(org.id)
            assert result["org_role"] == "org:admin"
            assert result["org_slug"] == "test-org"
            assert result["is_superadmin"] == False
            assert result["permissions"] == ["read:users", "write:users"]
            
            # Verify user's organization_id was updated
            updated_user = await db_session.scalar(select(User).where(User.clerk_user_id == "test-clerk-id"))
            assert updated_user.organization_id == org.id
    
    async def test_get_current_user_new(self, db_session, mock_auth_context):
        # Test get_current_user with a new user
        result = await get_current_user(mock_auth_context, db_session)
        
        # Verify a new user was created
        user = await db_session.scalar(select(User).where(User.clerk_user_id == "test-clerk-id"))
        assert user is not None
        assert result["id"] == str(user.id)
        assert result["clerk_user_id"] == "test-clerk-id"
        assert result["email"] is None
        assert result["full_name"] == ""
        assert result["organization_id"] is None  # No org exists yet
        assert result["org_role"] == "org:admin"
        assert result["org_slug"] == "test-org"
        assert result["is_superadmin"] == False
        assert result["permissions"] == ["read:users", "write:users"]
    
    async def test_get_current_user_superadmin(self, db_session, mock_auth_context):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Test get_current_user with superadmin
        with patch("app.security.clerk.SUPERADMINS", {"test-clerk-id"}):
            result = await get_current_user(mock_auth_context, db_session)
            assert result["is_superadmin"] == True
    
    async def test_role_required_superadmin(self, db_session, mock_auth_context):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create role_required dependency
        admin_required = role_required("admin")
        
        # Test with superadmin
        with patch("app.security.clerk.SUPERADMINS", {"test-clerk-id"}), \
             patch("app.security.clerk.get_current_user", return_value={
                 "id": str(user.id),
                 "clerk_user_id": "test-clerk-id",
                 "is_superadmin": True,
                 "org_role": "org:member"
             }):
            result = await admin_required()
            assert result["is_superadmin"] == True
    
    async def test_role_required_matching_role(self, db_session, mock_auth_context):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create role_required dependency
        admin_required = role_required("admin")
        
        # Test with matching role
        with patch("app.security.clerk.SUPERADMINS", set()), \
             patch("app.security.clerk.get_current_user", return_value={
                 "id": str(user.id),
                 "clerk_user_id": "test-clerk-id",
                 "is_superadmin": False,
                 "org_role": "org:admin"
             }):
            result = await admin_required()
            assert result["org_role"] == "org:admin"
    
    async def test_role_required_forbidden(self, db_session, mock_auth_context):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create role_required dependency
        admin_required = role_required("admin")
        
        # Test with non-matching role
        with patch("app.security.clerk.SUPERADMINS", set()), \
             patch("app.security.clerk.get_current_user", return_value={
                 "id": str(user.id),
                 "clerk_user_id": "test-clerk-id",
                 "is_superadmin": False,
                 "org_role": "org:member"
             }):
            with pytest.raises(HTTPException) as excinfo:
                await admin_required()
            assert excinfo.value.status_code == 403
            assert excinfo.value.detail == "Forbidden"


@pytest.mark.asyncio
class TestWebSocketAuth:
    async def test_get_current_user_ws_header(self, db_session, mock_auth_context):
        # Create mock websocket
        mock_websocket = MagicMock()
        mock_websocket.headers = {"authorization": "Bearer test-token"}
        mock_websocket.query_params = {}
        
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Test get_current_user_ws
        with patch("app.security.clerk._decode_clerk", return_value={}), \
             patch("app.security.clerk._claims_to_ctx", return_value=mock_auth_context), \
             patch("app.security.clerk.get_current_user", return_value={
                 "id": str(user.id),
                 "clerk_user_id": "test-clerk-id"
             }):
            result = await get_current_user_ws(mock_websocket, db_session)
            assert result["id"] == str(user.id)
            assert result["clerk_user_id"] == "test-clerk-id"
    
    async def test_get_current_user_ws_query_param(self, db_session, mock_auth_context):
        # Create mock websocket
        mock_websocket = MagicMock()
        mock_websocket.headers = {}
        mock_websocket.query_params = {"token": "test-token"}
        
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Test get_current_user_ws
        with patch("app.security.clerk._decode_clerk", return_value={}), \
             patch("app.security.clerk._claims_to_ctx", return_value=mock_auth_context), \
             patch("app.security.clerk.get_current_user", return_value={
                 "id": str(user.id),
                 "clerk_user_id": "test-clerk-id"
             }):
            result = await get_current_user_ws(mock_websocket, db_session)
            assert result["id"] == str(user.id)
            assert result["clerk_user_id"] == "test-clerk-id"
    
    async def test_get_current_user_ws_missing_token(self, db_session):
        # Create mock websocket
        mock_websocket = MagicMock()
        mock_websocket.headers = {}
        mock_websocket.query_params = {}
        mock_websocket.close = MagicMock()
        
        # Test get_current_user_ws with missing token
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user_ws(mock_websocket, db_session)
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "Missing token"
        mock_websocket.close.assert_called_once_with(code=4401)