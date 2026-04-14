import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import CustomerProfile
    from app.models.restaurant import Restaurant
    from app.models.menu_item import MenuItem


class OrderStatus(str, PyEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


ORDER_STATUS_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.PENDING:   [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.READY],
    OrderStatus.READY:     [OrderStatus.COMPLETED],
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELLED: [],
}


class Order(Base, TimestampMixin):
    """
    Order — Represents a confirmed food order placed by a customer at a restaurant.

    Why it exists:
        Once a customer checks out their cart, a permanent Order record is created.
        This is the core transaction record of the platform — it tracks what was
        ordered, from where, by whom, and the current state of
        preparation/delivery.

    What it stores:
        - customer_id         : who placed the order
        - restaurant_id       : which restaurant received the order
        - status              : current stage in the order lifecycle
                                (PENDING → CONFIRMED → PREPARING → READY →
                                COMPLETED, or CANCELLED at most stages).
                                Valid transitions are enforced by
                                ORDER_STATUS_TRANSITIONS above.
        - total_amount        : pre-calculated order total stored as a snapshot
                                so it never changes even if menu prices are
                                updated later
        - special_instructions: free-text notes from the customer
                                (e.g. "extra spicy", "no onions")

    Relationships:
        - CustomerProfile (many-to-one): An order belongs to one customer.
          RESTRICT on delete means a customer account cannot be wiped while
          their orders still exist — important for business and audit records.
        - Restaurant (many-to-one): An order targets one restaurant.
          Also RESTRICT on delete so a restaurant with order history can't
          be accidentally removed.
        - OrderItem (one-to-many): The individual line items (dishes + quantities)
          that make up this order. Deleting an order cascades to delete all
          its items, since items have no meaning without their parent order.
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)

    customer: Mapped["CustomerProfile"] = relationship(back_populates="orders")
    restaurant: Mapped["Restaurant"] = relationship(back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """
    OrderItem — A single line item within an order (one dish + quantity + price).

    Why it exists:
        An order can contain multiple different dishes. OrderItem breaks the
        order down into individual rows — one per distinct menu item selected.
        This is the standard "order lines" pattern used in e-commerce systems.

    What it stores:
        - order_id    : which order this line belongs to
        - menu_item_id: which dish was ordered (kept for display/reference)
        - quantity    : how many of this dish were ordered
        - unit_price  : the price of the dish AT THE TIME of ordering.
                        This is critical — menu prices can change over time,
                        but a historical order must always show what the
                        customer actually paid, not the current price.
        - subtotal    : unit_price × quantity, pre-calculated and stored so
                        order summaries are fast to render without recomputing

    Relationships:
        - Order (many-to-one): Each line item belongs to one order and is
          deleted when its parent order is deleted (CASCADE).
        - MenuItem (many-to-one): Points to the original menu item for
          displaying the dish name and image. RESTRICT on delete prevents
          removing a menu item that appears in any order history, ensuring
          past orders always have a valid reference.
    """

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="order_items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="order_items")

    @property
    def name(self) -> str | None:
        """Expose the menu item name so it can be serialised directly by OrderItemOut."""
        return self.menu_item.name if self.menu_item else None
