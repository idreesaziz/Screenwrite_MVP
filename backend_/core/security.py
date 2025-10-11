"""
JWT authentication and security utilities.

Handles Supabase JWT token validation and user extraction.
"""

import os
import jwt
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from .config import get_config


# Security scheme for Bearer token
security_scheme = HTTPBearer()


@lru_cache()
def get_jwt_secret() -> str:
    """Get JWT secret from configuration"""
    config = get_config()
    return config.auth.supabase_jwt_secret


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token from Supabase.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload containing user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        secret = get_jwt_secret()
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


def extract_user_from_token(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from decoded JWT payload.
    
    Args:
        payload: Decoded JWT payload
    
    Returns:
        Dictionary with user_id, email, session_id, role, etc.
    """
    return {
        "user_id": payload.get("sub"),  # User ID from 'sub' claim
        "email": payload.get("email"),
        "session_id": payload.get("session_id"),
        "role": payload.get("role", "user"),
        "raw_payload": payload  # Full payload for debugging
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["user_id"]
            ...
    
    Args:
        credentials: HTTP Bearer token from Authorization header
    
    Returns:
        User information dictionary
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user = extract_user_from_token(payload)
    
    if not user.get("user_id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid token: missing user_id"
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme, auto_error=False)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns None if no token provided.
    
    Usage:
        @app.get("/optional-auth")
        async def route(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                # Authenticated user
            else:
                # Anonymous user
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
