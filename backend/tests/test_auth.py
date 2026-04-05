import pytest
from app.auth import create_access_token, verify_token
from app.dependencies import get_current_user
from fastapi import HTTPException


class TestTokenGeneration:
    """Test JWT token generation and verification."""
    
    def test_create_access_token(self):
        """Test that access tokens are created correctly."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test that valid tokens are verified correctly."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "testuser"
    
    def test_verify_invalid_token(self):
        """Test that invalid tokens raise an error."""
        with pytest.raises(HTTPException):
            verify_token("invalid.token.here")
    
    def test_verify_expired_token(self):
        """Test that expired tokens raise an error."""
        from datetime import datetime, timedelta
        from app.config import settings
        from jose import jwt
        
        # Create an expired token
        data = {"sub": "testuser", "exp": datetime.utcnow() - timedelta(hours=1)}
        token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
        
        with pytest.raises(HTTPException):
            verify_token(token)
