"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


def generate_password_reset_token(email: str) -> str:
    """Backward-compatible helper that wraps ``create_password_reset_token``.

    Some modules still import :func:`generate_password_reset_token`; keep the
    thin wrapper so they continue to work without refactors.
    """
    return create_password_reset_token(email)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
        
    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> str:
    """Create a JWT access token.
    
    Args:
        subject: The subject (usually user ID) to include in the token
        expires_delta: Optional timedelta for token expiration
        token_type: Type of the token (e.g., 'access', 'refresh', 'reset')
        
    Returns:
        str: The encoded JWT token
        
    Raises:
        ValueError: If SECRET_KEY is not configured
    """
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY is not configured")
    
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
        "iat": now,
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        Optional[dict]: The decoded token payload if valid, None otherwise
    """
    if not token or not settings.SECRET_KEY:
        return None
        
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}
        )
        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create a password reset token.
    
    Args:
        email: The user's email address
        
    Returns:
        str: The password reset token
    """
    expires = timedelta(hours=24)  # Reset token valid for 24 hours
    return create_access_token(
        subject=email,
        expires_delta=expires,
        token_type="reset"
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token.
    
    Args:
        token: The password reset token
        
    Returns:
        Optional[str]: The email address if the token is valid, None otherwise
    """
    try:
        decoded_token = decode_token(token)
        if decoded_token is None:
            return None
        email = cast(Optional[str], decoded_token.get("sub"))
        return email
    except JWTError:
        return None
