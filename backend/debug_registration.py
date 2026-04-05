from app.database import get_db
from app.services.user_service import create_user, get_user_by_username, get_user_by_email
from app.models.schemas import UserCreate
from app.logging_config import logger

# Test the registration process step by step
db = next(get_db())

try:
    user_data = UserCreate(username='debuguser', email='debug@example.com', password='testpass123')

    print("Step 1: Checking if username exists...")
    existing_user = get_user_by_username(db, user_data.username)
    print(f"Username check result: {existing_user}")

    print("Step 2: Checking if email exists...")
    existing_user = get_user_by_email(db, user_data.email)
    print(f"Email check result: {existing_user}")

    print("Step 3: Creating user...")
    new_user = create_user(db, user_data)
    print(f"User creation result: {new_user}")

    print("Step 4: Committing transaction...")
    db.commit()
    print("Transaction committed successfully")

    db.close()
    print("SUCCESS: User registration completed")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    db.rollback()
    db.close()