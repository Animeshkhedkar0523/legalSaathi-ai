"""
JWT Authentication - Advanced token-based authentication
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Header
import secrets

from config import config

# Configuration
SECRET_KEY = getattr(config, "JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key")))
ALGORITHM = getattr(config, "JWT_ALGORITHM", os.getenv("JWT_ALGORITHM", "HS256"))
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(config, "ACCESS_TOKEN_EXPIRE_MINUTES", int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
REFRESH_TOKEN_EXPIRE_DAYS = getattr(config, "REFRESH_TOKEN_EXPIRE_DAYS", int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))



class JWTManager:
    """JWT token management - Production Grade"""
    
    # Token blacklist for revocation (in production, use Redis)
    _token_blacklist = set()
    
    @staticmethod
    def create_tokens(user_id: str, mobile: str) -> Dict[str, str]:
        """Create access and refresh tokens"""
        import secrets
        
        # Generate unique token IDs for revocation
        access_jti = secrets.token_urlsafe(32)
        refresh_jti = secrets.token_urlsafe(32)
        
        # Create access token
        access_payload = {
            "sub": user_id,
            "mobile": mobile,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "iat": datetime.now(timezone.utc),
            "jti": access_jti
        }
        
        # Create refresh token
        refresh_payload = {
            "sub": user_id,
            "mobile": mobile,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc),
            "jti": refresh_jti
        }
        
        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes in seconds
        }
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token (legacy, use create_tokens instead)"""
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
            
            # Check if token is blacklisted (revoked)
            if payload.get("jti") in JWTManager._token_blacklist:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            JWTManager._token_blacklist.add(payload.get("jti"))
            return True
        except:
            return False
    
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
