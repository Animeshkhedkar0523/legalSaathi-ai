"""
LegalSaathi Backend Services
"""

# Import all services
from backend.services.auth_service import (
    register_and_send_otp,
    verify_otp_and_login,
    verify_token,
    logout,
    get_user_by_mobile,
)

from backend.services.ai_service import AIService

from backend.services.ocr_service import OCRService

from backend.services.citation_service import CitationService

from backend.services.storage_service import StorageService

# Import all models
from backend.models.schemas import (
    Language,
    InterfaceMode,
    DocumentType,
    RiskLevel,
    UserRegister,
    User,
    LoginResult,
    Citation,
    RiskClause,
    DocumentResult,
    ScanDocumentResult,
    QAResponse,
)

__all__ = [
    # Auth
    "register_and_send_otp",
    "verify_otp_and_login",
    "verify_token",
    "logout",
    "get_user_by_mobile",
    # Services
    "AIService",
    "OCRService",
    "CitationService",
    "StorageService",
    # Models
    "Language",
    "InterfaceMode",
    "DocumentType",
    "RiskLevel",
    "UserRegister",
    "User",
    "LoginResult",
    "Citation",
    "RiskClause",
    "DocumentResult",
    "ScanDocumentResult",
    "QAResponse",
]
