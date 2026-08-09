"""Pydantic models for the User resource (ReqRes API)."""
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Request payload for creating a user."""

    name: str
    job: str


class UserResponse(BaseModel):
    """Single user resource, as returned (nested under "data") by GET /users/{id}."""

    model_config = ConfigDict(extra="ignore")

    id: int
    email: str
    first_name: str
    last_name: str
    avatar: str


class UserCreateResponse(BaseModel):
    """Response payload returned by POST /users."""

    id: str
    name: str
    job: str
    createdAt: str
