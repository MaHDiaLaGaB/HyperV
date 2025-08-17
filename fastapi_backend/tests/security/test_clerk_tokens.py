import os
import time
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from jose import jwt, jwk
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from app.security.clerk import _decode_clerk, _claims_to_ctx, require_clerk_claims


class TestClerkTokens:
    @pytest.fixture
    def rsa_key_pair(self):
        # Generate an RSA key pair for testing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Get the private key in PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get the public key in PEM format
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            "private_key": private_key,
            "public_key": public_key,
            "private_pem": private_pem,
            "public_pem": public_pem
        }
    
    @pytest.fixture
    def mock_jwks(self, rsa_key_pair):
        # Convert the public key to JWK format
        public_numbers = rsa_key_pair["public_key"].public_numbers()
        
        # Create a JWK from the public key
        jwk_dict = {
            "kty": "RSA",
            "kid": "test-kid",
            "use": "sig",
            "alg": "RS256",
            "n": jwk.base64url_encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder="big")),
            "e": jwk.base64url_encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder="big"))
        }
        
        return {
            "keys": [jwk_dict]
        }
    
    @pytest.fixture
    def create_token(self, rsa_key_pair):
        def _create_token(claims, headers=None):
            if headers is None:
                headers = {"kid": "test-kid", "alg": "RS256"}
            
            # Create a JWT with the given claims and headers
            token = jwt.encode(
                claims,
                rsa_key_pair["private_pem"],
                algorithm="RS256",
                headers=headers
            )
            
            return token
        
        return _create_token
    
    @pytest.mark.asyncio
    async def test_valid_token_decode(self, create_token, mock_jwks):
        # Create a valid token
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now + 3600,  # 1 hour from now
            "nbf": now - 60,    # 1 minute ago
            "iss": "https://test-clerk-issuer.clerk.accounts.dev",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users"]
        }
        token = create_token(claims)
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Decode the token
            decoded_claims = _decode_clerk(token)
            
            # Verify the claims
            assert decoded_claims["sub"] == "test-clerk-id"
            assert decoded_claims["azp"] == "test-azp"
            assert decoded_claims["org_id"] == "test-org-id"
            assert decoded_claims["org_role"] == "org:admin"
            assert decoded_claims["org_slug"] == "test-org"
            assert decoded_claims["org_permissions"] == ["read:users", "write:users"]
    
    @pytest.mark.asyncio
    async def test_expired_token(self, create_token, mock_jwks):
        # Create an expired token
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now - 3600,  # 1 hour ago
            "nbf": now - 7200,  # 2 hours ago
            "iss": "https://test-clerk-issuer.clerk.accounts.dev"
        }
        token = create_token(claims)
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Attempt to decode the token
            with pytest.raises(HTTPException) as excinfo:
                _decode_clerk(token)
            
            # Verify the error
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Token expired or not yet valid"
    
    @pytest.mark.asyncio
    async def test_future_token(self, create_token, mock_jwks):
        # Create a token that's not valid yet
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now + 7200,  # 2 hours from now
            "nbf": now + 3600,  # 1 hour from now
            "iss": "https://test-clerk-issuer.clerk.accounts.dev"
        }
        token = create_token(claims)
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Attempt to decode the token
            with pytest.raises(HTTPException) as excinfo:
                _decode_clerk(token)
            
            # Verify the error
            assert excinfo.value.status_code == 401
            assert excinfo.value.detail == "Token expired or not yet valid"
    
    @pytest.mark.asyncio
    async def test_invalid_issuer(self, create_token, mock_jwks):
        # Create a token with an invalid issuer
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now + 3600,  # 1 hour from now
            "nbf": now - 60,    # 1 minute ago
            "iss": "https://wrong-issuer.clerk.accounts.dev"
        }
        token = create_token(claims)
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Attempt to decode the token
            with pytest.raises(jwt.JWTError):
                _decode_clerk(token)
    
    @pytest.mark.asyncio
    async def test_invalid_signature(self, create_token, mock_jwks):
        # Create a token with valid claims
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now + 3600,  # 1 hour from now
            "nbf": now - 60,    # 1 minute ago
            "iss": "https://test-clerk-issuer.clerk.accounts.dev"
        }
        token = create_token(claims)
        
        # Tamper with the token
        parts = token.split('.')
        parts[1] = parts[1][:-5] + 'XXXXX'  # Change the payload
        tampered_token = '.'.join(parts)
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Attempt to decode the token
            with pytest.raises(jwt.JWTError):
                _decode_clerk(tampered_token)
    
    @pytest.mark.asyncio
    async def test_require_clerk_claims(self, create_token, mock_jwks):
        # Create a valid token
        now = int(time.time())
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "exp": now + 3600,  # 1 hour from now
            "nbf": now - 60,    # 1 minute ago
            "iss": "https://test-clerk-issuer.clerk.accounts.dev",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users"]
        }
        token = create_token(claims)
        
        # Create mock credentials
        mock_credentials = MagicMock()
        mock_credentials.credentials = token
        
        # Mock the JWKS endpoint and issuer
        with patch("app.security.clerk._jwks", return_value=mock_jwks), \
             patch("app.security.clerk.CLERK_ISSUER", "https://test-clerk-issuer.clerk.accounts.dev"), \
             patch("app.security.clerk.CLERK_PERMITTED_AZP", set()):
            
            # Call require_clerk_claims
            ctx = await require_clerk_claims(mock_credentials)
            
            # Verify the context
            assert ctx["sub"] == "test-clerk-id"
            assert ctx["azp"] == "test-azp"
            assert ctx["org_id"] == "test-org-id"
            assert ctx["org_role"] == "org:admin"
            assert ctx["org_slug"] == "test-org"
            assert ctx["org_permissions"] == ["read:users", "write:users"]
    
    @pytest.mark.asyncio
    async def test_claims_to_ctx_v2_format(self):
        # Test with v2 format claims
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "org_id": "test-org-id",
            "org_role": "org:admin",
            "org_slug": "test-org",
            "org_permissions": ["read:users", "write:users"]
        }
        
        ctx = _claims_to_ctx(claims)
        
        assert ctx["sub"] == "test-clerk-id"
        assert ctx["azp"] == "test-azp"
        assert ctx["org_id"] == "test-org-id"
        assert ctx["org_role"] == "org:admin"
        assert ctx["org_slug"] == "test-org"
        assert ctx["org_permissions"] == ["read:users", "write:users"]
    
    @pytest.mark.asyncio
    async def test_claims_to_ctx_legacy_format(self):
        # Test with legacy format claims
        claims = {
            "sub": "test-clerk-id",
            "azp": "test-azp",
            "o": {
                "id": "test-org-id",
                "rol": "org:admin",
                "slg": "test-org",
                "per": ["read:users", "write:users"]
            }
        }
        
        ctx = _claims_to_ctx(claims)
        
        assert ctx["sub"] == "test-clerk-id"
        assert ctx["azp"] == "test-azp"
        assert ctx["org_id"] == "test-org-id"
        assert ctx["org_role"] == "org:admin"
        assert ctx["org_slug"] == "test-org"
        assert ctx["org_permissions"] == ["read:users", "write:users"]