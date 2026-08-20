"""Pydantic models for the ReqRes /register and /login endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    token: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    token: str
