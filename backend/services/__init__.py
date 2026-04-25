# backend/services/__init__.py
from .ai_service import ai_service
from .citation_service import citation_service
from .ocr_service import ocr_service
from .storage_service import storage_service
from .auth_service import (
    register_and_send_otp,
    verify_otp_and_login,
    get_user_by_mobile,
    verify_token,
    logout,
)

__all__ = [
    "ai_service",
    "citation_service",
    "ocr_service",
    "storage_service",
    "register_and_send_otp",
    "verify_otp_and_login",
    "get_user_by_mobile",
    "verify_token",
    "logout",
]
