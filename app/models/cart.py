import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import CustomerProfile
    from app.models.menu_item import MenuItem


class CartItem(Base, TimestampMixin):
    """
    CartItem — Represents a single item a customer has added to their cart.

    Why it exists:
        Customers browse menus and add dishes before placing an order. This
        table acts as a temporary "shopping basket" that holds those selections
        until the customer is ready to check out.

    What it stores:
        - customer_id : which customer owns this cart entry
        - menu_item_id: which dish was added
        - quantity    : how many of that dish the customer wants

    Relationships:
        - CustomerProfile (many-to-one): Each CartItem belongs to one customer.
          The customer's full cart is the collection of all their CartItem rows.
          Deleted when the customer profile is deleted (CASCADE).
        - MenuItem (many-to-one): Each CartItem points to one menu item, letting
          us fetch the price and name when rendering the cart.
          Deleted if the menu item is removed (CASCADE).

    Constraint:
        A UniqueConstraint on (customer_id, menu_item_id) ensures a customer
        can't have two separate rows for the same dish — quantity is updated
        on the existing row instead of inserting a duplicate.
    """

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("customer_id", "menu_item_id", name="uq_cart_customer_item"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    customer: Mapped["CustomerProfile"] = relationship(back_populates="cart_items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="cart_items")
