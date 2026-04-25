"""
JWT Authentication - Advanced token-based authentication
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Header
import secrets

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRY_DAYS", 30)) * 24  # Convert days to hours
REFRESH_TOKEN_EXPIRE_DAYS = 90


class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode token without raising exceptions"""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


# Dependency for FastAPI
async def get_current_user_jwt(authorization: Optional[str] = Header(None)):
    """Dependency to verify JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    payload = JWTManager.verify_token(token)
    
    mobile = payload.get("mobile")
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    return {
        "mobile": mobile,
        "user_id": payload.get("sub"),
        "exp": payload.get("exp")
    }


# Token storage (in production, use Redis or database)
_REVOKED_TOKENS = set()


def revoke_token(token: str) -> None:
    """Add token to revocation list"""
    _REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked"""
    return token in _REVOKED_TOKENS
