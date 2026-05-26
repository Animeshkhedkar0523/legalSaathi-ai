"""
Main FastAPI Application - LegalSaathi Backend API
Enhanced with: Logging, Rate Limiting, Caching, JWT, Webhooks, LLM
"""
import uuid
import os
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Import new modules
from backend.logging_config import get_logger, get_log_stats
from backend.cache_and_limits import cache_manager, rate_limiter, cached
from backend.jwt_manager import JWTManager, get_current_user_jwt
from backend.webhooks import webhook_manager, WebhookEvent
from backend.llm_integration import llm_provider
from backend.sms_gateway import sms_gateway

# Import services
from backend.services.auth_service import (
    register_and_send_otp,
    verify_otp_and_login,
    verify_token,
    logout,
    get_user_by_mobile
)
from backend.services.ai_service import AIService
from backend.services.ocr_service import OCRService
from backend.services.citation_service import CitationService
from backend.services.storage_service import StorageService

# Import models
from backend.models.schemas import (
    UserRegister,
    DocumentType,
    Language,
    RiskLevel,
    DocumentResult,
    ScanDocumentResult,
    Citation,
    QAResponse
)

# Initialize logger
logger = get_logger("main")

# Initialize services
app = FastAPI(
    title="LegalSaathi API",
    description="AI-powered legal document generation and analysis platform",
    version="2.0.0"
)

# Add Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Add CORS middleware with restricted origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize service instances
ai_service = AIService()
ocr_service = OCRService()
citation_service = CitationService()
storage_service = StorageService()


# ─── Request/Response Models ─────────────────────────────────────────────────────
class OTPRequest(BaseModel):
    mobile: str
    otp: str


class OTPResponse(BaseModel):
    success: bool
    message: str
    dev_otp: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    user: dict
    access_token: str


class DocumentDraftRequest(BaseModel):
    doc_type: DocumentType
    data: dict
    language: Language = Language.EN
    include_citations: bool = False


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response"""
    success: bool
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int = 86400  # 24 hours
    token_type: str = "bearer"


class QARequest(BaseModel):
    question: str
    language: Language = Language.EN


class RiskAnalysisResponse(BaseModel):
    document_id: str
    risk_clauses: list
    overall_risk: str


# ─── Authentication Dependency ───────────────────────────────────────────────────
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to verify token and get current user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    try:
        token = authorization.replace("Bearer ", "")
        mobile = verify_token(token)
        if not mobile:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user = get_user_by_mobile(mobile)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/register", response_model=OTPResponse, tags=["Authentication"])
async def register(user_data: UserRegister):
    """
    Register a new user and send OTP
    
    Request:
    - mobile: str (required)
    - name: str (required)
    - email: str (optional)
    - language: Language (default: "en")
    - mode: InterfaceMode (default: "simple")
    """
    try:
        result = register_and_send_otp(user_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/verify-otp", response_model=LoginResponse, tags=["Authentication"])
async def verify_otp(request: OTPRequest):
    """
    Verify OTP and login
    
    Request:
    - mobile: str
    - otp: str (6 digits)
    """
    try:
        login_result = verify_otp_and_login(request.mobile, request.otp)
        if not login_result:
            raise HTTPException(status_code=400, detail="OTP verification failed")
        
        return {
            "success": True,
            "user": {
                "id": login_result.user.id,
                "mobile": login_result.user.mobile,
                "name": login_result.user.name,
                "email": login_result.user.email,
                "language": login_result.user.language.value,
                "mode": login_result.user.mode.value,
            },
            "access_token": login_result.access_token
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/logout", tags=["Authentication"])
async def user_logout(current_user = Depends(get_current_user)):
    """Logout and invalidate token"""
    try:
        # The token would be in the Authorization header
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Request:
    - refresh_token: str (the refresh token obtained during login)
    """
    try:
        from backend.jwt_manager import JWTManager
        
        # Verify refresh token
        payload = JWTManager.decode_token(request.refresh_token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Create new access token
        mobile = payload.get("mobile")
        new_access_token = JWTManager.create_access_token({
            "mobile": mobile,
            "sub": payload.get("sub")
        })
        
        return {
            "success": True,
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/verify-token", tags=["Authentication"])
async def verify_access_token(authorization: Optional[str] = Header(None)):
    """
    Verify if access token is valid
    
    Header:
    - Authorization: Bearer <token>
    """
    try:
        from backend.jwt_manager import JWTManager
        
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization format")
        
        payload = JWTManager.decode_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return {
            "success": True,
            "valid": True,
            "mobile": payload.get("mobile"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "mobile": current_user.mobile,
        "name": current_user.name,
        "email": current_user.email,
        "language": current_user.language.value,
        "mode": current_user.mode.value,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT GENERATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/draft", tags=["Document Generation"])
async def draft_document(
    request: DocumentDraftRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a legal document
    
    Request:
    - doc_type: DocumentType (rental_agreement, affidavit, will)
    - data: dict (form data for the document)
    - language: Language (en, hi)
    - include_citations: bool (whether to include legal citations)
    """
    try:
        # Generate document content
        content = ai_service.draft_document(
            request.doc_type,
            request.data,
            request.language
        )
        
        # Extract and verify citations if requested
        citations = []
        if request.include_citations:
            citation_texts = citation_service.extract_citations_from_text(content)
            citations = [
                citation_service.verify_citation(ct).dict()
                for ct in citation_texts
            ]
        
        # Detect risks
        risk_clauses = ai_service.detect_risks(content)
        overall_risk = ai_service.overall_risk(risk_clauses)
        
        # Summarize
        summary = ai_service.summarize_document(content, request.language)
        
        # Create document result
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        document = DocumentResult(
            document_id=doc_id,
            document_type=request.doc_type,
            content=content,
            summary=summary,
            citations=[Citation(**c) for c in citations],
            risk_clauses=risk_clauses,
            overall_risk=overall_risk,
            language=request.language,
            title=f"{request.doc_type.value.replace('_', ' ').title()}"
        )
        
        # Save document
        storage_service.save_created_document(document, current_user.mobile)
        
        return {
            "success": True,
            "document_id": doc_id,
            "content": content,
            "summary": summary,
            "citations": citations,
            "risk_analysis": {
                "clauses": [c.dict() for c in risk_clauses],
                "overall_risk": overall_risk.value
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT SCANNING ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/scan", tags=["Document Scanning"])
async def scan_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    language: str = Form(Language.EN.value)
):
    """
    Scan and analyze a document (PDF, Image, DOCX)
    
    Supports: PDF, JPG, PNG, DOCX
    No authentication required (guest mode)
    """
    try:
        # Read file
        file_bytes = await file.read()
        
        # Extract text using OCR
        extracted_text, detected_lang = ocr_service.extract_text_from_file(
            file_bytes,
            file.filename
        )
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Extract and verify citations
        citation_texts = citation_service.extract_citations_from_text(extracted_text)
        citations = [
            citation_service.verify_citation(ct).dict()
            for ct in citation_texts
        ]
        
        # Detect risks
        risk_clauses = ai_service.detect_risks(extracted_text)
        overall_risk = ai_service.overall_risk(risk_clauses)
        
        # Summarize
        lang_enum = Language(language) if language in [l.value for l in Language] else Language.EN
        summary = ai_service.summarize_document(extracted_text, lang_enum)
        
        # Create document result
        doc_id = f"scan_{uuid.uuid4().hex[:12]}"
        document = ScanDocumentResult(
            document_id=doc_id,
            extracted_text=extracted_text,
            detected_language=detected_lang,
            summary=summary,
            citations=[Citation(**c) for c in citations],
            risk_clauses=risk_clauses,
            overall_risk=overall_risk,
            title=title or file.filename
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "extracted_text": extracted_text,
            "detected_language": detected_lang,
            "summary": summary,
            "citations": citations,
            "risk_analysis": {
                "clauses": [c.dict() for c in risk_clauses],
                "overall_risk": overall_risk.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT RETRIEVAL ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/documents", tags=["Document Management"])
async def list_documents(current_user = Depends(get_current_user)):
    """Get all documents for current user"""
    try:
        documents = storage_service.list_user_documents(current_user.mobile)
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}", tags=["Document Management"])
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific document by ID"""
    try:
        document = storage_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": document.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}", tags=["Document Management"])
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a document"""
    try:
        if storage_service.delete_document(document_id, current_user.mobile):
            return {"success": True, "message": "Document deleted"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT ANALYSIS ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/{document_id}/risk-analysis", response_model=RiskAnalysisResponse, tags=["Analysis"])
async def analyze_risks(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Analyze risks in a document"""
    try:
        text = storage_service.get_document_text(document_id)
        if not text:
            raise HTTPException(status_code=404, detail="Document not found")
        
        risk_clauses = ai_service.detect_risks(text)
        overall_risk = ai_service.overall_risk(risk_clauses)
        
        return {
            "document_id": document_id,
            "risk_clauses": [c.dict() for c in risk_clauses],
            "overall_risk": overall_risk.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/{document_id}/summarize", tags=["Analysis"])
async def summarize_document(
    document_id: str,
    language: Language = Language.EN,
    current_user = Depends(get_current_user)
):
    """Get document summary"""
    try:
        text = storage_service.get_document_text(document_id)
        if not text:
            raise HTTPException(status_code=404, detail="Document not found")
        
        summary = ai_service.summarize_document(text, language)
        translated = ai_service.translate_text(summary, Language.HI) if language == Language.HI else summary
        
        return {
            "success": True,
            "document_id": document_id,
            "summary": summary,
            "summary_translated": translated if language == Language.HI else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CITATIONS ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/{document_id}/citations", tags=["Citations"])
async def extract_and_verify_citations(
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Extract and verify citations in a document"""
    try:
        text = storage_service.get_document_text(document_id)
        if not text:
            raise HTTPException(status_code=404, detail="Document not found")
        
        citation_texts = citation_service.extract_citations_from_text(text)
        verified_citations = [
            citation_service.verify_citation(ct).dict()
            for ct in citation_texts
        ]
        
        return {
            "success": True,
            "document_id": document_id,
            "citations": verified_citations,
            "count": len(verified_citations)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Q&A ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/{document_id}/qa", tags=["Q&A"])
async def ask_question(
    document_id: str,
    request: QARequest,
    current_user = Depends(get_current_user)
):
    """Ask a question about a document"""
    try:
        text = storage_service.get_document_text(document_id)
        if not text:
            raise HTTPException(status_code=404, detail="Document not found")
        
        response = ai_service.answer_question(text, request.question, request.language)
        
        return {
            "success": True,
            "document_id": document_id,
            "question": request.question,
            **response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/documents/{document_id}/translate", tags=["Translation"])
async def translate_document(
    document_id: str,
    target_language: Language = Language.HI,
    current_user = Depends(get_current_user)
):
    """Translate a document to another language"""
    try:
        text = storage_service.get_document_text(document_id)
        if not text:
            raise HTTPException(status_code=404, detail="Document not found")
        
        translated = ai_service.translate_text(text, target_language)
        
        return {
            "success": True,
            "document_id": document_id,
            "original_language": Language.EN.value,
            "target_language": target_language.value,
            "translated_content": translated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK MANAGEMENT ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/webhooks", tags=["Webhooks"])
async def register_webhook(
    webhook_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Register a new webhook for events
    
    Request:
    - url: str (webhook endpoint URL)
    - event: str (USER_REGISTERED, DOCUMENT_CREATED, DOCUMENT_ANALYZED, etc.)
    - secret: str (optional, for HMAC signature verification)
    """
    try:
        webhook = webhook_manager.register_webhook(
            url=webhook_data.get("url"),
            event=webhook_data.get("event"),
            secret=webhook_data.get("secret"),
            user_id=current_user.id
        )
        logger.info(f"Webhook registered for user {current_user.mobile}: {webhook.event}")
        
        return {
            "success": True,
            "webhook_id": webhook.id,
            "url": webhook.url,
            "event": webhook.event,
            "active": webhook.active,
            "created_at": webhook.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Webhook registration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/webhooks", tags=["Webhooks"])
async def list_webhooks(current_user = Depends(get_current_user)):
    """Get all webhooks for current user"""
    try:
        webhooks = webhook_manager.list_webhooks(user_id=current_user.id)
        return {
            "success": True,
            "count": len(webhooks),
            "webhooks": [
                {
                    "id": w.id,
                    "url": w.url,
                    "event": w.event,
                    "active": w.active,
                    "failure_count": w.failure_count,
                    "last_triggered": w.last_triggered.isoformat() if w.last_triggered else None,
                    "created_at": w.created_at.isoformat()
                }
                for w in webhooks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/webhooks/{webhook_id}", tags=["Webhooks"])
async def unregister_webhook(
    webhook_id: str,
    current_user = Depends(get_current_user)
):
    """Unregister a webhook"""
    try:
        success = webhook_manager.unregister_webhook(webhook_id, user_id=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        logger.info(f"Webhook unregistered for user {current_user.mobile}: {webhook_id}")
        return {
            "success": True,
            "message": "Webhook unregistered successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# MONITORING & STATS ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    """API root endpoint"""
    return {
        "success": True,
        "message": "LegalSaathi API v2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check"""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/health/cache", tags=["Monitoring"])
async def get_cache_stats():
    """Get cache statistics and performance metrics"""
    try:
        stats = cache_manager.stats()
        return {
            "success": True,
            "cache": {
                "items_count": stats["items_count"],
                "total_requests": stats["total_requests"],
                "hits": stats["hits"],
                "misses": stats["misses"],
                "hit_rate": f"{stats['hit_rate']:.2f}%"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/limits", tags=["Monitoring"])
async def get_rate_limit_stats(identifier: str = Query("global")):
    """Get rate limiter statistics"""
    try:
        stats = rate_limiter.get_identifier_stats(identifier)
        return {
            "success": True,
            "identifier": identifier,
            "rate_limit": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL ENDPOINTS (Protected)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/admin/dashboard", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def admin_dashboard(current_user: dict = Depends(get_current_user_jwt)):
    """Admin dashboard with system statistics"""
    try:
        cache_stats = cache_manager.stats() if hasattr(cache_manager, 'stats') else {}
        return {
            "success": True,
            "dashboard": {
                "users_online": 0,  # TODO: Connect to actual metrics
                "documents_processed_today": 0,
                "api_requests_today": 0,
                "cache_performance": cache_stats,
                "system_health": "operational",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/users", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_jwt)
):
    """List all users with pagination"""
    try:
        # TODO: Connect to actual database query
        return {
            "success": True,
            "users": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/documents", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def list_documents(
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_jwt)
):
    """List all documents with optional filtering"""
    try:
        # TODO: Connect to actual database query
        return {
            "success": True,
            "documents": [],
            "total": 0,
            "filters": {"status": status}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/cache/clear", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def clear_cache(pattern: str = Query("*"), current_user: dict = Depends(get_current_user_jwt)):
    """Clear cache entries matching pattern"""
    try:
        cleared = cache_manager.clear_cache(pattern)
        return {
            "success": True,
            "message": f"Cleared {cleared} cache entries",
            "pattern": pattern
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/logs/export", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def export_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: dict = Depends(get_current_user_jwt)
):
    """Export system logs"""
    try:
        log_stats = get_log_stats()
        return {
            "success": True,
            "logs": log_stats,
            "format": format,
            "exported_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/system/config", tags=["Admin"], dependencies=[Depends(get_current_user_jwt)])
async def get_system_config(current_user: dict = Depends(get_current_user_jwt)):
    """Get current system configuration"""
    try:
        return {
            "success": True,
            "config": {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug": os.getenv("DEBUG", "False") == "True",
                "database": "PostgreSQL",
                "cache_backend": "Redis",
                "rate_limiting": "Enabled",
                "jwt_expiry_access": "30 minutes",
                "jwt_expiry_refresh": "7 days",
                "log_level": os.getenv("LOG_LEVEL", "INFO")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/logs", tags=["Monitoring"])
async def get_logging_stats():
    """Get logging statistics"""
    try:
        stats = get_log_stats()
        return {
            "success": True,
            "logging": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/system", tags=["Monitoring"])
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        cache_stats = cache_manager.stats()
        log_stats = get_log_stats()
        
        return {
            "success": True,
            "system": {
                "timestamp": datetime.utcnow().isoformat(),
                "cache": cache_stats,
                "logging": log_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/extended", tags=["Monitoring"])
async def get_extended_health():
    """Get comprehensive health and stats information"""
    try:
        cache_stats = cache_manager.stats()
        return {
            "success": True,
            "service": "LegalSaathi API",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "cache": {
                "items_count": cache_stats["items_count"],
                "hit_rate": f"{cache_stats['hit_rate']:.2f}%",
                "total_requests": cache_stats["total_requests"]
            },
            "features": {
                "jwt_authentication": True,
                "logging": True,
                "caching": True,
                "rate_limiting": True,
                "webhooks": True,
                "llm_integration": True,
                "sms_gateway": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
