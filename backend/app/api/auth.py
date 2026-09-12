"""
Batu Networks ERP - Authentication API Router
Module: backend/app/api/auth.py

Provides login, persona switching, and user verification endpoints for enterprise multi-tenancy.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.core.auth import (
    DEFAULT_USERS,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["User Authentication & RBAC"])

class LoginRequest(BaseModel):
    username: str = Field(..., examples=["sg_purchaser"])
    password: str = Field(..., examples=["PurchasingPass2026!"])

class UserProfile(BaseModel):
    username: str
    full_name: str
    email: str
    role: str
    entity_code: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    Authenticates user and returns an HS256 JWT access token.
    For development and demo testing, supports demo passwords.
    """
    user_record = DEFAULT_USERS.get(req.username)
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau kata sandi tidak valid."
        )

    # In enterprise demo mode, allow matching username or standard pass
    # Default valid demo passwords:
    demo_passwords = {
        "admin": "BatuAdmin2026!",
        "sg_purchaser": "PurchasingPass2026!",
        "sg_sales": "SalesPass2026!",
        "vn_logistics": "LogisticsPass2026!",
        "sg_treasurer": "TreasuryPass2026!",
        "compliance_auditor": "AuditorPass2026!"
    }
    expected_pass = demo_passwords.get(req.username, "BatuPass2026!")
    if req.password != expected_pass and req.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak cocok."
        )

    token = create_access_token({
        "sub": user_record["username"],
        "name": user_record["full_name"],
        "role": user_record["role"],
        "entity": user_record["entity_code"],
        "email": user_record["email"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user_record["username"],
            "full_name": user_record["full_name"],
            "email": user_record["email"],
            "role": user_record["role"],
            "entity_code": user_record["entity_code"]
        }
    }

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the profile of the currently authenticated operator."""
    return {
        "username": current_user["username"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "entity_code": current_user["entity_code"]
    }

@router.get("/demo-personas", response_model=List[UserProfile])
async def list_demo_personas():
    """Returns available role personas for instant frontend switching and testing."""
    return [
        {
            "username": u["username"],
            "full_name": u["full_name"],
            "email": u["email"],
            "role": u["role"],
            "entity_code": u["entity_code"]
        }
        for u in DEFAULT_USERS.values()
    ]
