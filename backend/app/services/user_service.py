from sqlalchemy.orm import Session
from app.models.models import User
from app.models.schemas import UserCreate, UserResponse
from app.auth import hash_password
from app.logging_config import logger


def create_user(db: Session, user: UserCreate) -> UserResponse:
    """Create a new user"""
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.flush()  # Flush to get the ID without committing
    db.refresh(db_user)

    logger.info("User created", username=user.username, user_id=db_user.id)

    # Convert to response format
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None
    )


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Authenticate user with username and password"""
    from app.auth import verify_password

    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user