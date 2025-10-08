"""
Authentication middleware for FastAPI backend.
Verifies Supabase JWT tokens and extracts user information.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    print("⚠️  WARNING: SUPABASE_JWT_SECRET not set. Authentication will fail.")

security = HTTPBearer()


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Verify Supabase JWT token and return payload.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        dict: JWT payload containing user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(payload: dict = Depends(verify_jwt)) -> dict:
    """
    Extract user information from verified JWT payload.
    
    Args:
        payload: Verified JWT payload
        
    Returns:
        dict: User information including:
            - user_id: Supabase user UUID
            - email: User's email address
            - session_id: Current session ID (for GCS path isolation)
            - role: User role (usually "authenticated")
    """
    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")
    
    # Get session ID from payload (used for GCS path isolation)
    # Supabase includes session_id in the JWT
    session_id = payload.get("session_id", user_id)  # Fallback to user_id if no session_id
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: missing user ID"
        )
    
    return {
        "user_id": user_id,
        "email": email,
        "role": role,
        "session_id": session_id,
        "full_payload": payload  # Include full payload for debugging
    }
