"""
JWT authentication utilities
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from ..config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, ensuring we don't break multi-byte characters
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        # If bcrypt still complains, try with a shorter password
        if "72 bytes" in str(e):
            password = password[:50]  # Use a safe shorter length
            return pwd_context.hash(password)
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials = Depends(security)) -> str:
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials from request
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
