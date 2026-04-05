import pytest
from app.services.user_service import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    authenticate_user,
)
from app.models.schemas import UserCreate


class TestUserService:
    """Test user service functions."""
    
    def test_create_user(self, db_session, test_user_data):
        """Test creating a new user."""
        user_create = UserCreate(**test_user_data)
        user = create_user(db_session, user_create)
        
        assert user is not None
        assert user.username == test_user_data["username"]
        assert user.email == test_user_data["email"]
        assert user.is_active is True
    
    def test_get_user_by_username(self, db_session, test_user_data):
        """Test retrieving user by username."""
        user_create = UserCreate(**test_user_data)
        create_user(db_session, user_create)
        
        user = get_user_by_username(db_session, test_user_data["username"])
        assert user is not None
        assert user.username == test_user_data["username"]
    
    def test_get_user_by_email(self, db_session, test_user_data):
        """Test retrieving user by email."""
        user_create = UserCreate(**test_user_data)
        create_user(db_session, user_create)
        
        user = get_user_by_email(db_session, test_user_data["email"])
        assert user is not None
        assert user.email == test_user_data["email"]
    
    def test_authenticate_user_success(self, db_session, test_user_data):
        """Test successful user authentication."""
        user_create = UserCreate(**test_user_data)
        create_user(db_session, user_create)
        
        user = authenticate_user(
            db_session,
            test_user_data["username"],
            test_user_data["password"]
        )
        assert user is not None
        assert user.username == test_user_data["username"]
    
    def test_authenticate_user_wrong_password(self, db_session, test_user_data):
        """Test authentication with wrong password."""
        user_create = UserCreate(**test_user_data)
        create_user(db_session, user_create)
        
        user = authenticate_user(
            db_session,
            test_user_data["username"],
            "wrong_password"
        )
        assert user is None
    
    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication of non-existent user."""
        user = authenticate_user(db_session, "nonexistent", "password")
        assert user is None
    
    def test_duplicate_username(self, db_session, test_user_data):
        """Test that duplicate usernames are rejected."""
        user_create = UserCreate(**test_user_data)
        create_user(db_session, user_create)
        
        # Attempt to create user with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        user_create_dup = UserCreate(**duplicate_data)
        
        # This should fail in the database constraint
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            create_user(db_session, user_create_dup)
            db_session.commit()
