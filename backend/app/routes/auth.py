"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from ..database import Database
from ..utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.options("/login")
@router.options("/register")
@router.options("/refresh")
@router.options("/me")
async def options_handler():
    """Handle OPTIONS requests for CORS preflight"""
    return {"status": "ok"}


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If email already exists
    """
    db = Database.get_db()
    
    # Validate password length
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Truncate password if it exceeds bcrypt's 72-byte limit
    password = user_data.password
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "created_at": None  # Will be set by MongoDB
    }
    
    # Insert user
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_minutes * 60
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Login with email and password
    
    Args:
        credentials: User login credentials
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    db = Database.get_db()
    
    # Find user by email
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": user["email"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user_id: str = Depends(get_current_user)):
    """
    Refresh access token
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        New JWT access token
    """
    db = Database.get_db()
    
    # Get user details
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(current_user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": current_user_id, "email": user["email"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_minutes * 60
    )


@router.get("/me")
async def get_current_user_info(current_user_id: str = Depends(get_current_user)):
    """
    Get current user information
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        User information (without password)
    """
    db = Database.get_db()
    
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(current_user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Remove sensitive data
    user.pop("hashed_password", None)
    user["_id"] = str(user["_id"])
    
    return user
