"""Security utilities for authentication and password handling.

This module provides:
- Password hashing and verification using bcrypt
- JWT access token creation and validation
- Refresh token generation with secure hashing
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Token type identifiers
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def get_password_hash(plain: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        plain: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password.

    Args:
        plain: The plaintext password to verify.
        hashed: The bcrypt-hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: str, role: str, email: str = "") -> str:
    """Create a JWT access token.

    Args:
        subject: The user ID to encode in the token.
        role: The user's role (customer/owner).
        email: The user's email address.

    Returns:
        Encoded JWT access token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "role": role,
        "email": email,
        "exp": expire,
        "type": TOKEN_TYPE_ACCESS,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token() -> tuple[str, str, datetime]:
    """Generate a new refresh token.

    Returns:
        A tuple containing:
        - raw: The raw token to send to the client
        - token_hash: SHA-256 hash to store in database
        - expires_at: Token expiration datetime (UTC)
    """
    raw = str(uuid.uuid4())
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return raw, token_hash, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload.

    Raises:
        JWTError: If the token is invalid or not an access token.
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise JWTError("Not an access token")
    return payload
