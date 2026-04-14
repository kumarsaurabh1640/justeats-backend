import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User, CustomerProfile
    from app.models.menu_item import MenuItem
    from app.models.order import Order


class Restaurant(Base, TimestampMixin):
    """
    Restaurant — The core listing for a restaurant on the platform.

    Why it exists:
        This is the primary entity that customers browse. A restaurant is
        created and managed by a user with the "owner" role. It acts as
        the hub that ties together the menu, incoming orders, and customer
        favourites.

    What it stores:
        - owner_id                  : which user account manages this restaurant
        - name, cuisine_type,
          location, description,
          image_url                 : public-facing info shown to browsing
                                      customers on the restaurant listing page
        - is_active                 : lets owners temporarily pause their
                                      restaurant (e.g. on holiday) without
                                      deleting it, so no new orders come in
        - rating                    : average customer rating stored as Numeric
                                      (e.g. 4.75) for display and sorting

    Relationships:
        - User / owner (many-to-one): A restaurant is owned by one user.
          If the owner account is deleted, the restaurant is deleted too
          (CASCADE) — a restaurant can't exist without an owner.
        - MenuItem (one-to-many)    : All dishes that this restaurant sells.
          Items are deleted when the restaurant is deleted (CASCADE), since
          menu items have no meaning without their restaurant.
        - Order (one-to-many)       : All orders ever placed at this restaurant.
          Uses RESTRICT on delete so a restaurant with order history can't
          be accidentally removed and orphan transaction records.
        - FavouriteRestaurant
          (one-to-many)            : Records of customers who have saved this
                                      restaurant as a favourite. Deleted when
                                      the restaurant is deleted (CASCADE).
    """

    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cuisine_type: Mapped[Optional[str]] = mapped_column(String(100))
    location: Mapped[Optional[str]] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))

    owner: Mapped["User"] = relationship(back_populates="restaurants")
    menu_items: Mapped[List["MenuItem"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship(back_populates="restaurant")
    favourited_by: Mapped[List["FavouriteRestaurant"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")


class FavouriteRestaurant(Base):
    """
    FavouriteRestaurant — A join table recording which customers have saved
                          which restaurants as favourites.

    Why it exists:
        Customers want to bookmark restaurants they like for quick re-ordering.
        Rather than storing a list inside a column (which is hard to query),
        a proper join table is used so each favourite is a queryable,
        indexable row. This implements a many-to-many relationship between
        customers and restaurants.

    What it stores:
        - customer_id  : the customer who added the favourite
        - restaurant_id: the restaurant that was favourited
        (No extra fields needed — the existence of the row is the data.)

    Relationships:
        - CustomerProfile (many-to-one): Belongs to one customer. Deleted when
          the customer profile is deleted (CASCADE), so no orphaned favourites
          remain after an account is removed.
        - Restaurant (many-to-one): Points to one restaurant. Deleted when the
          restaurant is deleted (CASCADE), so favourites don't reference
          listings that no longer exist.

    Constraint:
        A UniqueConstraint on (customer_id, restaurant_id) ensures a customer
        can only favourite a restaurant once — duplicate rows are rejected
        at the database level.
    """

    __tablename__ = "favourite_restaurants"
    __table_args__ = (UniqueConstraint("customer_id", "restaurant_id", name="uq_fav_customer_restaurant"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    customer: Mapped["CustomerProfile"] = relationship(back_populates="favourite_restaurants")
    restaurant: Mapped["Restaurant"] = relationship(back_populates="favourited_by")
