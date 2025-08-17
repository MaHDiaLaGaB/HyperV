import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy import select
from app.security.clerk import get_current_user, role_required, CurrentUser
from app.models.users.users import User
from app.models.users.organization import Organization
from app.schemas.enums import ClientType


@pytest.mark.asyncio
class TestClerkPermissions:
    async def test_superadmin_access(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a mock auth context
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": None,
            "org_role": None,
            "org_slug": None,
            "org_permissions": []
        }
        
        # Test with superadmin
        with patch("app.security.clerk.SUPERADMINS", {"test-clerk-id"}):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["is_superadmin"] == True
            
            # Test role_required with superadmin
            admin_required = role_required("admin")
            result = await admin_required(current_user)
            assert result == current_user
            
            # Test role_required with a different role
            editor_required = role_required("editor")
            result = await editor_required(current_user)
            assert result == current_user
    
    async def test_role_based_access(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a mock auth context with admin role
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users"]
        }
        
        # Test with non-superadmin but admin role
        with patch("app.security.clerk.SUPERADMINS", set()):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["is_superadmin"] == False
            assert current_user["org_role"] == "org:admin"
            
            # Test role_required with matching role
            admin_required = role_required("admin")
            result = await admin_required(current_user)
            assert result == current_user
            
            # Test role_required with non-matching role
            editor_required = role_required("editor")
            with pytest.raises(HTTPException) as excinfo:
                await editor_required(current_user)
            assert excinfo.value.status_code == 403
            assert excinfo.value.detail == "Forbidden"
    
    async def test_multiple_allowed_roles(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a mock auth context with editor role
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:editor",
            "org_slug": "test-org",
            "org_permissions": ["read:users"]
        }
        
        # Test with non-superadmin but editor role
        with patch("app.security.clerk.SUPERADMINS", set()):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["is_superadmin"] == False
            assert current_user["org_role"] == "org:editor"
            
            # Test role_required with multiple allowed roles
            multi_role_required = role_required("admin", "editor", "viewer")
            result = await multi_role_required(current_user)
            assert result == current_user
            
            # Test role_required with non-matching roles
            restricted_role_required = role_required("admin", "owner")
            with pytest.raises(HTTPException) as excinfo:
                await restricted_role_required(current_user)
            assert excinfo.value.status_code == 403
            assert excinfo.value.detail == "Forbidden"
    
    async def test_no_role(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a mock auth context with no role
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": None,
            "org_role": None,
            "org_slug": None,
            "org_permissions": []
        }
        
        # Test with non-superadmin and no role
        with patch("app.security.clerk.SUPERADMINS", set()):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["is_superadmin"] == False
            assert current_user["org_role"] is None
            
            # Test role_required with any role
            any_role_required = role_required("admin", "editor", "viewer")
            with pytest.raises(HTTPException) as excinfo:
                await any_role_required(current_user)
            assert excinfo.value.status_code == 403
            assert excinfo.value.detail == "Forbidden"
    
    async def test_permissions_from_clerk(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a mock auth context with permissions
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users", "delete:users"]
        }
        
        # Test permissions are correctly passed through
        with patch("app.security.clerk.SUPERADMINS", set()):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["permissions"] == ["read:users", "write:users", "delete:users"]
    
    async def test_organization_linking(self, db_session):
        # Create a test user
        user = User(clerk_user_id="test-clerk-id", email="test@example.com", full_name="Test User")
        db_session.add(user)
        
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
        await db_session.refresh(user)
        await db_session.refresh(org)
        
        # Create a mock auth context with organization
        mock_auth_context = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users"]
        }
        
        # Test organization linking
        with patch("app.security.clerk.SUPERADMINS", set()):
            current_user = await get_current_user(mock_auth_context, db_session)
            assert current_user["organization_id"] == str(org.id)
            
            # Verify user's organization_id was updated
            updated_user = await db_session.scalar(select(User).where(User.clerk_user_id == "test-clerk-id"))
            assert updated_user.organization_id == org.id