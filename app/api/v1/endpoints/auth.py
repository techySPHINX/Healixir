from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials, exceptions as firebase_exceptions

from app.core.config import settings
from app.core.security import create_access_token

# Initialize Firebase Admin SDK
if not firebase_admin._apps:  # Avoid using protected `_apps`
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

router = APIRouter()

# Request and response models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    email: str
    full_name: Optional[str] = None
    token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    try:
        # Create user in Firebase Authentication
        firebase_user = firebase_auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.full_name or "",
        )
        # Generate JWT token
        token = create_access_token(data={"sub": firebase_user.email})
        return UserResponse(email=firebase_user.email, full_name=firebase_user.display_name, token=token)
    except firebase_exceptions.AlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    except firebase_exceptions.FirebaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Firebase error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error registering user: {str(e)}")


@router.post("/login", response_model=UserResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Authenticate user by email
        firebase_user = firebase_auth.get_user_by_email(form_data.username)
        # Note: Firebase does not handle passwords, so implement password verification if required.
        # Generate JWT token
        token = create_access_token(data={"sub": firebase_user.email})
        return UserResponse(email=firebase_user.email, full_name=firebase_user.display_name, token=token)
    except firebase_exceptions.NotFoundError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    except firebase_exceptions.FirebaseError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Firebase error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error logging in user: {str(e)}")
