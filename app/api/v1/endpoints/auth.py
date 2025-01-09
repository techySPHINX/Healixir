from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials, exceptions as firebase_exceptions
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.crud import create_user, get_user_by_firebase_uid
from app.database import init_db  # Ensure database session dependency

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: str  # Include role in user creation

class UserResponse(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str
    token: str

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(init_db())):
    try:
        # Create user in Firebase Authentication
        firebase_user = firebase_auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.full_name or "",
        )

        # Save user in the database
        user_data = {
            "firebase_uid": firebase_user.uid,
            "email": firebase_user.email,
            "full_name": firebase_user.display_name,
            "role": user.role,
        }
        db_user = create_user(db, user_data)

        # Generate JWT token
        token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
        return UserResponse(email=db_user.email, full_name=db_user.full_name, role=db_user.role, token=token)
    except firebase_exceptions.AlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    except firebase_exceptions.FirebaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Firebase error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error registering user: {str(e)}")

@router.post("/login", response_model=UserResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(init_db())):
    try:
        firebase_user = firebase_auth.get_user_by_email(form_data.username)

        # Retrieve user details from the database
        db_user = get_user_by_firebase_uid(db, firebase_user.uid)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # Generate JWT token
        token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
        return UserResponse(email=db_user.email, full_name=db_user.full_name, role=db_user.role, token=token)
    except firebase_exceptions.FirebaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Firebase error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error logging in user: {str(e)}")
