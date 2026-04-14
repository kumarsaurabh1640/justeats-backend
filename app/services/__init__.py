"""
Customer & Owner Profile Services
===================================

Helper functions for working with user profiles. These are shared
across multiple routers to keep things DRY (Don't Repeat Yourself).

Why a separate services module?
- Avoids copy-pasting the same profile lookup code everywhere
- Makes it easy to change profile logic in one place
- Keeps our router files focused on handling HTTP requests
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import CustomerProfile, OwnerProfile, User


# ─── Customer profile helpers ───────────────────────────────────────────


async def get_customer_profile(user: User, db: AsyncSession) -> CustomerProfile:
    """
    Look up a customer's profile from the database.

    Every customer should have a profile to place orders, manage their cart,
    and save preferences. If they don't have one yet, we tell them to create
    it first (they can do this by visiting their profile page).

    Args:
        user: The logged-in user whose profile we need
        db: Database connection to run queries

    Returns:
        The customer's profile record

    Raises:
        HTTPException 404: When the user hasn't set up their profile yet
    """
    # Try to find an existing profile for this user
    profile = await db.scalar(
        select(CustomerProfile).where(CustomerProfile.user_id == user.id)
    )

    # No profile? Let them know they need to create one first
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a profile yet. Please visit your profile page to set one up.",
        )

    return profile


async def get_or_create_profile(user: User, db: AsyncSession) -> CustomerProfile:
    """
    Get a customer's profile, creating one automatically if needed.

    This is the "friendly" version - instead of throwing an error when
    there's no profile, we just create a blank one. Perfect for endpoints
    like the profile page where we want to show something even for new users.

    Args:
        user: The logged-in user
        db: Database connection

    Returns:
        Either the existing profile or a freshly created empty one
    """
    # Check if they already have a profile
    existing_profile = await db.scalar(
        select(CustomerProfile).where(CustomerProfile.user_id == user.id)
    )

    if existing_profile:
        return existing_profile

    # No profile yet - let's create a blank one for them
    new_profile = CustomerProfile(user_id=user.id)
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)  # Get the auto-generated ID and timestamps

    return new_profile


# ─── Owner profile helpers ───────────────────────────────────────────

async def get_or_create_owner_profile(user: User, db: AsyncSession) -> OwnerProfile:
    """
    Get a restaurant owner's profile, creating one automatically if needed.

    Works the same as get_or_create_profile but for the owner_profiles table.
    Owners can store their name, phone, bio, and food preferences here.

    Args:
        user: The logged-in owner
        db: Database connection

    Returns:
        Either the existing owner profile or a freshly created empty one
    """
    existing_profile = await db.scalar(
        select(OwnerProfile).where(OwnerProfile.user_id == user.id)
    )

    if existing_profile:
        return existing_profile

    # First visit — create a blank profile so the page has something to show
    new_profile = OwnerProfile(user_id=user.id)
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)

    return new_profile
