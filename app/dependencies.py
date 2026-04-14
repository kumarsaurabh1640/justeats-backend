"""FastAPI dependency injection utilities.

This module provides reusable dependencies for:
- User authentication via JWT tokens
- Role-based access control
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Retrieve the current authenticated user from JWT token.

    Args:
        token: Bearer token from Authorization header.
        db: Database session.

    Returns:
        The authenticated User instance.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
        HTTPException: 403 if user account is disabled.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    return user


def require_role(*roles: str) -> Callable:
    """Create a dependency that requires specific user roles.

    Args:
        *roles: One or more role names that are allowed access.

    Returns:
        An async dependency function that validates user roles.

    Example:
        @router.post("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("owner"))):
            ...
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {', '.join(roles)}",
            )
        return current_user
    return _check
