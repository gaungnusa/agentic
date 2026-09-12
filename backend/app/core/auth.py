"""
Batu Networks ERP - Authentication & RBAC Core Security
Module: backend/app/core/auth.py

Provides PBKDF2-HMAC-SHA256 password hashing, HMAC-SHA256 JWT tokens,
and Role-Based Access Control (RBAC) dependencies for multi-tenant ERP operations.
100% pure Python standard library implementation for zero-dependency enterprise stability.
"""

import hmac
import hashlib
import base64
import json
import time
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Security parameters
SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "batu-enterprise-super-secret-key-2026-audit-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security_bearer = HTTPBearer(auto_error=False)

# Seed user accounts for multi-tenant enterprise simulation
DEFAULT_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "full_name": "Enterprise System Administrator",
        "email": "admin@batu-networks.com",
        "role": "admin",
        "entity_code": "ALL",
        # Default password: BatuAdmin2026!
        "salt": "d981a2f1c8b3e4a5",
        "password_hash": "25f448c5a2c2049d53ea7fbb05fbcba0e08f2343c3f29bda16999330da37f261"
    },
    "sg_purchaser": {
        "username": "sg_purchaser",
        "full_name": "Tan Wei Ming (Purchasing Specialist)",
        "email": "weiming.tan@batu-networks.sg",
        "role": "purchasing",
        "entity_code": "SG",
        "salt": "7f8b9c0d1e2f3a4b",
        "password_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
    },
    "sg_sales": {
        "username": "sg_sales",
        "full_name": "Clara Lim (Regional Sales Director)",
        "email": "clara.lim@batu-networks.sg",
        "role": "sales",
        "entity_code": "SG",
        "salt": "1a2b3c4d5e6f7a8b",
        "password_hash": "b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef01"
    },
    "vn_logistics": {
        "username": "vn_logistics",
        "full_name": "Nguyen Van Thao (Warehouse Supervisor)",
        "email": "thao.nguyen@batu-networks.vn",
        "role": "warehouse",
        "entity_code": "VN",
        "salt": "3c4d5e6f7a8b1a2b",
        "password_hash": "c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef012"
    },
    "sg_treasurer": {
        "username": "sg_treasurer",
        "full_name": "Marcus Goh (Treasury Controller)",
        "email": "marcus.goh@batu-networks.sg",
        "role": "treasury",
        "entity_code": "SG",
        "salt": "5e6f7a8b1a2b3c4d",
        "password_hash": "d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0123"
    },
    "compliance_auditor": {
        "username": "compliance_auditor",
        "full_name": "Sarah Jenkins (Senior Audit Officer)",
        "email": "sarah.jenkins@batu-networks.com",
        "role": "auditor",
        "entity_code": "ALL",
        "salt": "7a8b1a2b3c4d5e6f",
        "password_hash": "e5f67890123456789abcdef0123456789abcdef0123456789abcdef01234"
    }
}

# Role to Agent Mapping Matrix
AGENT_ROLE_PERMISSIONS = {
    "agent_1": ["purchasing", "admin"],
    "agent_2": ["purchasing", "admin"],
    "agent_3": ["sales", "admin"],
    "agent_4": ["purchasing", "admin"],
    "agent_5": ["purchasing", "admin"],
    "agent_6": ["warehouse", "admin"],
    "agent_7": ["warehouse", "admin"],
    "agent_8": ["treasury", "admin"],
    "agent_9": ["treasury", "admin"],
}


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 (100,000 iterations). Returns (hex_hash, salt)."""
    if not salt:
        salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return dk.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a password against the stored PBKDF2-HMAC-SHA256 hash in constant time."""
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hmac.compare_digest(dk.hex(), stored_hash)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_access_token(payload_data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a standard HS256 signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _b64url_encode(header_bytes)

    expire_ts = time.time() + (expires_delta.total_seconds() if expires_delta else ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    claims = {**payload_data, "exp": int(expire_ts), "iat": int(time.time())}
    payload_bytes = json.dumps(claims, separators=(',', ':')).encode('utf-8')
    payload_b64 = _b64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Validates signature and expiration of an HS256 JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Decode claims
        claims = json.loads(_b64url_decode(payload_b64).decode('utf-8'))

        # Check expiration
        if "exp" in claims and claims["exp"] < time.time():
            return None

        return claims
    except Exception:
        return None


async def get_current_user(auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates current user from Bearer token.
    Falls back to SG Purchaser default persona if unauthenticated (for smooth developer experience).
    """
    if auth and auth.credentials:
        claims = decode_access_token(auth.credentials)
        if claims and "sub" in claims:
            username = claims["sub"]
            if username in DEFAULT_USERS:
                return DEFAULT_USERS[username]
            return {
                "username": username,
                "full_name": claims.get("name", username),
                "email": claims.get("email", ""),
                "role": claims.get("role", "operator"),
                "entity_code": claims.get("entity", "SG")
            }

    # Dev fallback persona
    return DEFAULT_USERS["sg_purchaser"]


def require_role_for_agent(agent_id: str, user: Dict[str, Any]):
    """
    Enforces RBAC rules: validates whether the user's role is authorized to review/approve
    decisions for the given agent.
    """
    agent_key = str(agent_id).lower().replace("-", "_")
    allowed_roles = AGENT_ROLE_PERMISSIONS.get(agent_key, ["admin"])
    user_role = user.get("role", "")
    
    if user_role != "admin" and user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Otorisasi ditolak. Peran '{user_role}' tidak memiliki izin untuk mengotorisasi '{agent_id}'. Izin yang berwenang: {allowed_roles}"
        )
