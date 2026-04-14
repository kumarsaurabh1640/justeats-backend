"""
Profile Schemas
================

Pydantic models for reading and updating user profiles.
Both customers and owners have their own profile type.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Customer Profile
# ──────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    """Fields a customer can update on their profile. All fields are optional."""

    full_name: Optional[str] = Field(None, max_length=200, description="Customer's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    favourite_cuisine: Optional[str] = Field(None, max_length=200, description="Preferred type of cuisine")
    dietary_restrictions: Optional[str] = Field(
        None, max_length=500,
        description="Any dietary needs, e.g. 'vegetarian, no nuts'"
    )


class ProfileOut(BaseModel):
    """Customer profile data returned from the API."""

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: Optional[str]
    phone: Optional[str]
    favourite_cuisine: Optional[str]
    dietary_restrictions: Optional[str]

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Owner Profile
# ──────────────────────────────────────────────

class OwnerProfileUpdate(BaseModel):
    """Fields a restaurant owner can update on their profile. All fields are optional."""

    full_name: Optional[str] = Field(None, max_length=200, description="Owner's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    bio: Optional[str] = Field(
        None, max_length=1000,
        description="A short introduction shown on restaurant listings"
    )
    favourite_cuisine: Optional[str] = Field(None, max_length=200, description="Preferred type of cuisine")
    dietary_restrictions: Optional[str] = Field(
        None, max_length=500,
        description="Any dietary needs, e.g. 'vegan, gluten-free'"
    )


class OwnerProfileOut(BaseModel):
    """Owner profile data returned from the API."""

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    favourite_cuisine: Optional[str]
    dietary_restrictions: Optional[str]

    model_config = {"from_attributes": True}
