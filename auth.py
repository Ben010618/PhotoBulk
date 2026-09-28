"""
KameraPh Server-Side Authentication & Session Security Engine
-------------------------------------------------------------
Provides secure authentication, password hashing, and role checks:
  - Super Admin (System & Engine Management)
  - Studio Admin (Batch Operations, Billing & Exports)
  - Session verification via signed tokens
"""

import os
import time
import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends, Header
from init_db import get_db_connection, hash_password, verify_password

JWT_SECRET = os.environ.get("JWT_SECRET", "kameraph_super_secret_jwt_key_philippines_2026")


def create_access_token(user_data: Dict[str, Any], expires_in_seconds: int = 86400 * 7) -> str:
    """Generates an HMAC-SHA256 signed stateless session token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "studio_id": user_data.get("studio_id"),
        "exp": int(time.time()) + expires_in_seconds
    }
    
    hdr_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    pay_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), f"{hdr_b64}.{pay_b64}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{hdr_b64}.{pay_b64}.{sig_b64}"


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies HMAC signature and token expiration."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        hdr_b64, pay_b64, sig_b64 = parts
        
        expected_sig = hmac.new(JWT_SECRET.encode(), f"{hdr_b64}.{pay_b64}".encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + "==")
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload = json.loads(base64.urlsafe_b64decode(pay_b64 + "==").decode())
        if payload.get("exp", 0) < int(time.time()):
            return None
            
        return payload
    except Exception:
        return None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Validates user email and password against the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1 LIMIT 1;", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
        
    if not verify_password(password, user["password_hash"]):
        return None
        
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "studio_id": user["studio_id"]
    }


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extracts authenticated user from Authorization header or 'token' query param if present."""
    token = None
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
    elif "token" in request.query_params:
        token = request.query_params["token"].strip()

    if token:
        payload = verify_token(token)
        if payload:
            return payload
    return None


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency: Requires a valid authenticated session."""
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    return user


async def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency: Requires super_admin role for admin endpoints."""
    # Allow local development bypass only if DEBUG is True and a special dev-admin key is provided
    is_debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
    auth_header = request.headers.get("Authorization") or ""
    admin_secret = os.environ.get("ADMIN_API_KEY", "")
    if is_debug and admin_secret and auth_header == f"Bearer {admin_secret}":
        return {"id": "admin-system", "email": "admin@kameraph.com", "role": "super_admin"}

    user = await get_current_user(request)
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Forbidden. Super administrator privileges required.")
    return user
