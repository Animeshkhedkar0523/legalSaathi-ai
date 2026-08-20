"""
Data models and schemas for LegalSaathi
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class Language(str, Enum):
    EN = "en"
    HI = "hi"


class InterfaceMode(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"


class DocumentType(str, Enum):
    RENTAL_AGREEMENT = "rental_agreement"
    AFFIDAVIT = "affidavit"
    WILL = "will"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# ── AUTH MODELS ───────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    mobile: str
    name: str
    language: Language
    mode: InterfaceMode
    email: Optional[str] = None


class User(BaseModel):
    id: str
    mobile: str
    name: str
    email: Optional[str] = None
    language: Language
    mode: InterfaceMode
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LoginResult(BaseModel):
    user: User
    access_token: str
    otp_dev: Optional[str] = None  # For development/testing only


# ── CITATION MODELS ───────────────────────────────────────────────────────────
class Citation(BaseModel):
    citation_text: str
    case_name: Optional[str] = None
    year: Optional[int] = None
    is_verified: bool = False
    source: Optional[str] = None  # Link to Indian Kanoon or similar


# ── RISK DETECTION MODELS ─────────────────────────────────────────────────────
class RiskClause(BaseModel):
    clause_text: str
    risk_level: RiskLevel
    risk_reason: str
    suggestion: Optional[str] = None


# ── DOCUMENT MODELS ───────────────────────────────────────────────────────────
class DocumentResult(BaseModel):
    document_id: str
    document_type: DocumentType
    content: str
    summary: str
    summary_translated: Optional[str] = None
    citations: List[Citation] = []
    risk_clauses: List[RiskClause] = []
    overall_risk: RiskLevel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    language: Language
    title: Optional[str] = None


class ScanDocumentResult(BaseModel):
    document_id: str
    extracted_text: str
    detected_language: str
    summary: str
    summary_translated: Optional[str] = None
    citations: List[Citation] = []
    risk_clauses: List[RiskClause] = []
    overall_risk: RiskLevel
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    title: Optional[str] = None


class CreateDocumentRequest(BaseModel):
    document_type: DocumentType
    data: dict
    language: Language
    user_id: str


# ── Q&A MODELS ────────────────────────────────────────────────────────────────
class QAResponse(BaseModel):
    answer: str
    relevant_clauses: List[str] = []
    confidence: float = 0.0


class LegalQAResponse(BaseModel):
    answer: str
    legal_domain: str
    intent: str
    confidence: float = 0.0
    requires_lawyer: bool = False
    sources: List[Union[str, Dict[str, Any]]] = []
    disclaimer: str = "LegalSaathi provides general legal information based on document content, not professional legal advice. Consult a qualified advocate for specific legal decisions."


class QARequest(BaseModel):
    question: str
    language: Language = Language.EN

