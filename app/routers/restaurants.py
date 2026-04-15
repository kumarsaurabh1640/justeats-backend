"""Restaurant management endpoints.

Provides CRUD operations for restaurants:
- Public: List and view restaurants
- Owner-only: Create, update, and delete restaurants
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_role
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.restaurant import RestaurantCreate, RestaurantOut, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=List[RestaurantOut])
async def list_restaurants(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[Restaurant]:
    """List all active restaurants.

    Args:
        search: Optional search term matched against restaurant name, location, AND
                cuisine type (case-insensitive, partial match). A single query covers
                all three fields so customers can type e.g. "Italian" to find Italian
                restaurants without needing a separate cuisine filter parameter.

    Returns:
        List of active restaurants, sorted by name.
    """
    from sqlalchemy import or_

    query = select(Restaurant).where(Restaurant.is_active.is_(True))

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Restaurant.name.ilike(term),
                Restaurant.location.ilike(term),
                Restaurant.cuisine_type.ilike(term),
            )
        )

    result = await db.scalars(query.order_by(Restaurant.name))
    return list(result.all())


@router.get("/mine", response_model=List[RestaurantOut])
async def list_my_restaurants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> List[Restaurant]:
    """List all restaurants owned by the current owner (including inactive)."""
    result = await db.scalars(
        select(Restaurant)
        .where(Restaurant.owner_id == current_user.id)
        .order_by(Restaurant.name)
    )
    return list(result.all())


@router.get("/{restaurant_id:uuid}", response_model=RestaurantOut)
async def get_restaurant(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Restaurant:
    """Get a specific restaurant by ID.

    Args:
        restaurant_id: The restaurant's unique identifier.

    Returns:
        The restaurant details.

    Raises:
        HTTPException: 404 if restaurant not found.
    """
    restaurant = await db.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    return restaurant


@router.post("", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    payload: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> Restaurant:
    """Create a new restaurant (Owner only).

    Args:
        payload: Restaurant details.

    Returns:
        The newly created restaurant.
    """
    restaurant = Restaurant(**payload.model_dump(), owner_id=current_user.id)
    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)
    return restaurant


@router.patch("/{restaurant_id:uuid}", response_model=RestaurantOut)
async def update_restaurant(
    restaurant_id: uuid.UUID,
    payload: RestaurantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> Restaurant:
    """Update a restaurant (Owner only).

    Only the restaurant owner can update their restaurant.

    Args:
        restaurant_id: The restaurant's unique identifier.
        payload: Fields to update.

    Returns:
        The updated restaurant.

    Raises:
        HTTPException: 404 if not found, 403 if not owner.
    """
    restaurant = await db.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your restaurant",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)
    await db.commit()
    await db.refresh(restaurant)
    return restaurant


@router.delete("/{restaurant_id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("owner")),
) -> None:
    """Delete a restaurant (Owner only).

    Only the restaurant owner can delete their restaurant.
    This also cascades to delete all associated menu items.

    Args:
        restaurant_id: The restaurant's unique identifier.

    Raises:
        HTTPException: 404 if not found, 403 if not owner.
    """
    restaurant = await db.get(Restaurant, restaurant_id)
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your restaurant",
        )
    await db.delete(restaurant)
    await db.commit()
