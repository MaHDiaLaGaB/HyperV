import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from fastapi import status
from sqlalchemy import select
from app.models.users.users import User
from app.models.users.organization import Organization
from app.schemas.enums import ClientType


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_me_endpoint(self, test_client):
        # Mock the get_current_user dependency
        mock_user = {
            "id": "test-id",
            "clerk_user_id": "test-clerk-id",
            "email": "test@example.com",
            "full_name": "Test User",
            "organization_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "is_superadmin": False,
            "permissions": ["read:users", "write:users"]
        }
        
        with patch("app.security.clerk.get_current_user", return_value=mock_user):
            # Override the dependency in the app
            from app.routes.router.auth import get_current_user as original_get_current_user
            from app.main import app
            
            app.dependency_overrides[original_get_current_user] = lambda: mock_user
            
            # Test the /auth/me endpoint
            response = await test_client.get("/auth/me")
            
            # Reset the dependency override
            app.dependency_overrides.pop(original_get_current_user)
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == "test-id"
            assert data["clerk_user_id"] == "test-clerk-id"
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
            assert data["organization_id"] == "test-org-id"
            assert data["org_role"] == "org:admin"
            assert data["org_slug"] == "test-org"
            assert data["is_superadmin"] == False
            assert data["permissions"] == ["read:users", "write:users"]
    
    async def test_me_endpoint_unauthorized(self, test_client):
        # Test without authentication
        response = await test_client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_check_admin_endpoint(self, test_client):
        # Mock the role_required dependency
        mock_user = {
            "id": "test-id",
            "clerk_user_id": "test-clerk-id",
            "email": "test@example.com",
            "full_name": "Test User",
            "organization_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "is_superadmin": False,
            "permissions": ["read:users", "write:users"]
        }
        
        # Import the role_required function and create a mock
        from app.routes.router.auth import role_required
        from app.main import app
        
        # Create a mock for the role_required dependency
        mock_admin_required = lambda: mock_user
        
        # Override the dependency in the app
        with patch("app.security.clerk.role_required", return_value=mock_admin_required):
            # Test the /auth/check-admin endpoint
            response = await test_client.get("/auth/check-admin")
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["ok"] == True
            assert data["user_id"] == "test-id"
            assert data["org_role"] == "org:admin"
    
    async def test_check_admin_endpoint_forbidden(self, test_client):
        # Import the role_required function
        from app.routes.router.auth import role_required
        from app.main import app
        
        # Create a mock that raises a 403 error
        from fastapi import HTTPException
        
        def mock_admin_required():
            raise HTTPException(status_code=403, detail="Forbidden")
        
        # Override the dependency in the app
        with patch("app.security.clerk.role_required", return_value=lambda: mock_admin_required()):
            # Test the /auth/check-admin endpoint
            response = await test_client.get("/auth/check-admin")
            
            # Verify the response
            assert response.status_code == status.HTTP_403_FORBIDDEN
            data = response.json()
            assert data["detail"] == "Forbidden"


@pytest.mark.asyncio
class TestAuthIntegration:
    async def test_user_creation_on_first_auth(self, test_client, db_session):
        # Mock auth context
        mock_auth_context = {
            "sub": "new-clerk-id",
            "azp": "test-azp",
            "org_id": None,
            "org_role": None,
            "org_slug": None,
            "org_permissions": []
        }
        
        # Mock the require_clerk_claims dependency
        with patch("app.security.clerk.require_clerk_claims", return_value=mock_auth_context), \
             patch("app.security.clerk.SUPERADMINS", set()):
            
            # Override the dependency in the app
            from app.security.clerk import require_clerk_claims as original_require_clerk_claims
            from app.main import app
            
            app.dependency_overrides[original_require_clerk_claims] = lambda: mock_auth_context
            
            # Make a request to an authenticated endpoint
            response = await test_client.get("/auth/me")
            
            # Reset the dependency override
            app.dependency_overrides.pop(original_require_clerk_claims)
            
            # Verify a new user was created
            user = await db_session.scalar(select(User).where(User.clerk_user_id == "new-clerk-id"))
            assert user is not None
            assert user.clerk_user_id == "new-clerk-id"
            assert user.email is None
            assert user.full_name == ""
    
    async def test_organization_linking(self, test_client, db_session):
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
        
        # Mock auth context with organization
        mock_auth_context = {
            "sub": "new-clerk-id-with-org",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:member",
            "org_slug": "test-org",
            "org_permissions": ["read:users"]
        }
        
        # Mock the require_clerk_claims dependency
        with patch("app.security.clerk.require_clerk_claims", return_value=mock_auth_context), \
             patch("app.security.clerk.SUPERADMINS", set()):
            
            # Override the dependency in the app
            from app.security.clerk import require_clerk_claims as original_require_clerk_claims
            from app.main import app
            
            app.dependency_overrides[original_require_clerk_claims] = lambda: mock_auth_context
            
            # Make a request to an authenticated endpoint
            response = await test_client.get("/auth/me")
            
            # Reset the dependency override
            app.dependency_overrides.pop(original_require_clerk_claims)
            
            # Verify a new user was created and linked to the organization
            user = await db_session.scalar(select(User).where(User.clerk_user_id == "new-clerk-id-with-org"))
            assert user is not None
            assert user.clerk_user_id == "new-clerk-id-with-org"
            assert user.organization_id == org.id
            
            # Verify the response includes organization info
            data = response.json()
            assert data["organization_id"] == str(org.id)
            assert data["org_role"] == "org:member"
            assert data["org_slug"] == "test-org"