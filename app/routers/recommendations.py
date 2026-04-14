"""Personalized restaurant recommendations endpoint.

Provides recommendations based on:
1. Customer's order history (most frequently ordered restaurants)
2. Fallback to top-rated restaurants for new users
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_role
from app.models.order import Order, OrderStatus
from app.models.restaurant import Restaurant
from app.models.user import CustomerProfile, User
from app.schemas.restaurant import RestaurantOut

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

# Maximum number of recommendations to return
MAX_RECOMMENDATIONS = 10


@router.get("", response_model=List[RestaurantOut])
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("customer")),
) -> List[Restaurant]:
    """Get personalized restaurant recommendations.

    For customers with order history:
        Returns restaurants ordered from most frequently, sorted by order count.

    For new customers (no orders):
        Returns top-rated active restaurants.

    Returns:
        List of up to 10 recommended restaurants.
    """
    # Get customer profile
    profile = await db.scalar(
        select(CustomerProfile).where(CustomerProfile.user_id == current_user.id)
    )

    if profile:
        # Find restaurants ordered from, grouped by frequency
        order_counts = await db.execute(
            select(
                Order.restaurant_id,
                func.count(Order.id).label("order_count"),
            )
            .where(
                Order.customer_id == profile.id,
                Order.status == OrderStatus.COMPLETED,
            )
            .group_by(Order.restaurant_id)
            .order_by(desc("order_count"))
            .limit(MAX_RECOMMENDATIONS)
        )
        rows = order_counts.all()

        if rows:
            # Fetch restaurant details and maintain order
            restaurant_ids = [row.restaurant_id for row in rows]
            restaurants = (
                await db.scalars(
                    select(Restaurant).where(
                        Restaurant.id.in_(restaurant_ids),
                        Restaurant.is_active.is_(True),
                    )
                )
            ).all()

            # Sort by original order count ranking
            id_to_rank = {
                row.restaurant_id: idx for idx, row in enumerate(rows)
            }
            return sorted(
                restaurants,
                key=lambda r: id_to_rank.get(r.id, 999),
            )

    # Fallback: top-rated restaurants
    top_rated = await db.scalars(
        select(Restaurant)
        .where(
            Restaurant.is_active.is_(True),
            Restaurant.rating.isnot(None),
        )
        .order_by(desc(Restaurant.rating))
        .limit(MAX_RECOMMENDATIONS)
    )
    return list(top_rated.all())
