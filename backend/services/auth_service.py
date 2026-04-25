"""
Authentication Service - Handles user registration, OTP, and login
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from backend.models.schemas import User, UserRegister, LoginResult, Language, InterfaceMode
import json
import os

# ── In-Memory Database (for development) ───────────────────────────────────────
_USERS_DB = {}  # {mobile: user_dict}
_OTP_DB = {}    # {mobile: {"otp": code, "expires": timestamp}}
_TOKENS_DB = {} # {token: mobile}

# ── Config ─────────────────────────────────────────────────────────────────────
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes
TOKEN_EXPIRY_DAYS = 30


def _generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def _generate_token() -> str:
    """Generate a unique token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


def _generate_user_id() -> str:
    """Generate a unique user ID"""
    return f"user_{datetime.utcnow().timestamp()}_{_generate_token()[:8]}"


def register_and_send_otp(data: UserRegister) -> dict:
    """
    Register a user and send OTP to their mobile.
    Returns OTP for development (should be sent via SMS in production).
    """
    mobile = data.mobile
    
    # Check if user already exists
    if mobile in _USERS_DB:
        user = _USERS_DB[mobile]
        # Update language and mode if provided
        user.update({
            "language": data.language.value,
            "mode": data.mode.value,
            "updated_at": datetime.utcnow().isoformat()
        })
    else:
        # Create new user (not yet verified)
        _USERS_DB[mobile] = {
            "id": _generate_user_id(),
            "mobile": mobile,
            "name": data.name,
            "email": data.email,
            "language": data.language.value,
            "mode": data.mode.value,
            "verified": False,
            "created_at": datetime.utcnow().isoformat()
        }
    
    # Generate and store OTP
    otp = _generate_otp()
    _OTP_DB[mobile] = {
        "otp": otp,
        "expires": (datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)).isoformat()
    }
    
    # In production, send OTP via SMS gateway (Twilio, AWS SNS, etc.)
    # For now, return it for development/testing
    return {
        "success": True,
        "message": f"OTP sent to {mobile}",
        "dev_otp": otp  # Remove in production!
    }


def verify_otp_and_login(mobile: str, otp: str) -> Optional[LoginResult]:
    """
    Verify OTP and return login credentials
    """
    # Check if OTP exists and is not expired
    if mobile not in _OTP_DB:
        raise ValueError("OTP not found. Please register first.")
    
    otp_data = _OTP_DB[mobile]
    expires_at = datetime.fromisoformat(otp_data["expires"])
    
    if datetime.utcnow() > expires_at:
        del _OTP_DB[mobile]
        raise ValueError("OTP has expired. Please request a new one.")
    
    if otp_data["otp"] != otp:
        raise ValueError("Invalid OTP. Please try again.")
    
    # OTP is valid, get or create user
    if mobile not in _USERS_DB:
        raise ValueError("User not found. Please register first.")
    
    user_data = _USERS_DB[mobile]
    user = User(
        id=user_data["id"],
        mobile=user_data["mobile"],
        name=user_data["name"],
        email=user_data.get("email"),
        language=Language(user_data["language"]),
        mode=InterfaceMode(user_data["mode"]),
        created_at=datetime.fromisoformat(user_data["created_at"])
    )
    
    # Mark user as verified
    user_data["verified"] = True
    user_data["verified_at"] = datetime.utcnow().isoformat()
    
    # Generate token
    token = _generate_token()
    _TOKENS_DB[token] = mobile
    
    # Remove OTP after successful verification
    del _OTP_DB[mobile]
    
    return LoginResult(
        user=user,
        access_token=token
    )


def get_user_by_mobile(mobile: str) -> Optional[User]:
    """Get user by mobile number"""
    if mobile not in _USERS_DB:
        return None
    
    user_data = _USERS_DB[mobile]
    return User(
        id=user_data["id"],
        mobile=user_data["mobile"],
        name=user_data["name"],
        email=user_data.get("email"),
        language=Language(user_data["language"]),
        mode=InterfaceMode(user_data["mode"]),
        created_at=datetime.fromisoformat(user_data["created_at"])
    )


def verify_token(token: str) -> Optional[str]:
    """Verify if token is valid and return mobile number"""
    return _TOKENS_DB.get(token)


def logout(token: str) -> bool:
    """Logout user by removing token"""
    if token in _TOKENS_DB:
        del _TOKENS_DB[token]
        return True
    return False
