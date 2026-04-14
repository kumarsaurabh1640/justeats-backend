"""
Profile Management Endpoints
==============================

Handles profile read/update for both user roles:
- /profile           → Customer profile (food prefs, dietary info, etc.)
- /profile/owner     → Owner profile (bio, contact, food prefs, etc.)

Both endpoints auto-create a blank profile on first access, so users
never hit a confusing "not found" error when they first open their profile page.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_role
from app.models.user import CustomerProfile, OwnerProfile, User
from app.schemas.profile import (
    OwnerProfileOut,
    OwnerProfileUpdate,
    ProfileOut,
    ProfileUpdate,
)
from app.services import get_or_create_owner_profile, get_or_create_profile

router = APIRouter(prefix="/profile", tags=["profile"])


# ─── Customer endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=ProfileOut)
async def get_customer_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("customer")),
) -> CustomerProfile:
    """
    Get the logged-in customer's profile.

    Returns personal info and food preferences. Creates a blank profile
    automatically if this is the customer's first time here.
    """
    return await get_or_create_profile(current_user, db)


@router.patch("", response_model=ProfileOut)
async def update_customer_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("customer")),
) -> CustomerProfile:
    """
    Update the logged-in customer's profile.

    Only sends the fields you want to change — everything else stays the same.
    For example, you can update just the phone number without touching anything else.
    """
    profile = await get_or_create_profile(current_user, db)

    # Apply only the fields that were actually sent in the request
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


# ─── Owner endpoints ──────────────────────────────────────────────────────────

@router.get("/owner", response_model=OwnerProfileOut)
async def get_owner_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> OwnerProfile:
    """
    Get the logged-in owner's profile.

    Returns contact info, bio, and personal food preferences.
    Creates a blank profile automatically on first visit.
    """
    return await get_or_create_owner_profile(current_user, db)


@router.patch("/owner", response_model=OwnerProfileOut)
async def update_owner_profile(
    payload: OwnerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> OwnerProfile:
    """
    Update the logged-in owner's profile.

    Owners can set their name, phone, a short bio (shown on restaurant pages),
    and their own cuisine/dietary preferences.

    Only the fields you include get updated — partial updates are fully supported.
    """
    profile = await get_or_create_owner_profile(current_user, db)

    # Apply only the fields that were actually sent in the request
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile
