import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base, TimestampMixin):
    """
    RefreshToken — Stores hashed JWT refresh tokens for persistent login sessions.

    Why it exists:
        JWTs (access tokens) are stateless — once issued, the server has no way
        to invalidate them before they expire. Refresh tokens solve this: they
        are long-lived tokens stored server-side (hashed) that are exchanged for
        new short-lived access tokens. Storing them here lets us revoke individual
        sessions (e.g. "log out this device") or all sessions (e.g. on password
        change) without waiting for access tokens to naturally expire.

    What it stores:
        - user_id    : whose session this token belongs to
        - token_hash : a SHA-256 hash of the raw token. The raw token is NEVER
                       stored — only its hash — so a database leak can't be
                       used to hijack sessions directly
        - expires_at : when this token becomes invalid regardless of revocation,
                       acting as an absolute time limit on session age
        - revoked    : True once the token has been explicitly invalidated
                       (e.g. on logout or if suspicious activity is detected),
                       so it can't be used even if it hasn't expired yet

    Relationships:
        - User (many-to-one): Each token belongs to one user. A user can have
          multiple active tokens simultaneously — one per device or browser tab.
          All tokens for a user are deleted when their account is deleted
          (CASCADE), ensuring no orphaned session data remains.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
