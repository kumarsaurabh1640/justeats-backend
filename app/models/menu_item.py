import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant
    from app.models.order import OrderItem
    from app.models.cart import CartItem


class MenuItem(Base, TimestampMixin):
    """
    MenuItem — Represents a single dish or product offered by a restaurant.

    Why it exists:
        Restaurants need to publish what they sell so customers can browse and
        order. Each row is one item on the menu — a burger, a pizza, a drink,
        etc. Owners manage these directly through the menu management interface.

    What it stores:
        - restaurant_id: which restaurant this item belongs to
        - name, description, image_url: display info shown to customers
        - price         : cost of the item (Numeric for exact decimal precision,
                          avoids floating-point rounding errors in money)
        - category      : groups items (e.g. "Starters", "Mains") for browsing
        - is_available  : lets owners temporarily hide items (e.g. sold out)
                          without deleting them
        - is_special    : flags the item as a chef's special or promotion
        - order_count   : how many times this item has been ordered in total,
                          used by the recommendations engine to rank popular dishes

    Relationships:
        - Restaurant (many-to-one): Every menu item belongs to exactly one
          restaurant. If the restaurant is deleted, all its items are deleted
          too (CASCADE), since items have no meaning without their restaurant.
        - OrderItem (one-to-many): When a customer orders this item, an
          OrderItem row is created that snapshots the price at that moment.
          RESTRICT on delete prevents removing an item that exists in order
          history, preserving the integrity of past orders.
        - CartItem (one-to-many): Customers can add this item to their cart
          before placing an order. Deleted from carts if the item is removed
          (CASCADE).
    """

    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_special: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="menu_item")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="menu_item")
