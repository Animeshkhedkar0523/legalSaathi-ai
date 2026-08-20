# 🏗️ Architecture & API Documentation - LegalSaathi

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Web Interface                   │
│              (Frontend - React/HTML/CSS)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐    ┌──────────┐   ┌──────────┐
    │  Auth  │    │   AI     │   │   OCR    │
    │Service │    │ Service  │   │ Service  │
    └────────┘    └──────────┘   └──────────┘
        │               │               │
        │      ┌────────┼────────┐      │
        │      ▼        ▼        ▼      │
        │   ┌─────────────────────┐    │
        │   │  Citation Service   │    │
        │   └─────────────────────┘    │
        │               │               │
        └───────────────┼───────────────┘
                        ▼
            ┌──────────────────────┐
            │ Storage Service      │
            │ (In-Memory/DB)       │
            └──────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
    ┌─────────┐   ┌─────────┐   ┌──────────────┐
    │  Users  │   │Documents│   │ User-Doc Map │
    └─────────┘   └─────────┘   └──────────────┘
```

## Service Architecture

### 1. Authentication Service (`auth_service.py`)

**Purpose**: User registration, OTP verification, and session management

**Key Functions**:
```python
register_and_send_otp(data: UserRegister) -> dict
# Registers user and sends OTP (SMS in production)

verify_otp_and_login(mobile: str, otp: str) -> LoginResult
# Verifies OTP and returns login credentials

verify_token(token: str) -> Optional[str]
# Validates session token

logout(token: str) -> bool
# Logs out user by removing token
```

**Data Models**:
```python
UserRegister        # Registration input
User               # User object
LoginResult        # Login response with token
```

**Flow**:
1. User submits registration with mobile + OTP
2. System generates 6-digit OTP
3. OTP sent via SMS (or shown in dev mode)
4. User enters OTP
5. Verification succeeds → Token generated
6. Token used for session management

---

### 2. AI Service (`ai_service.py`)

**Purpose**: Document generation, analysis, risk detection, and Q&A

**Key Functions**:
```python
draft_document(doc_type, data, language, citations) -> str
# Generates legal document from user input

detect_risks(text: str) -> List[RiskClause]
# Identifies risky clauses in document

overall_risk(risk_clauses: List[RiskClause]) -> RiskLevel
# Calculates overall risk level

summarize_document(text: str, language: Language) -> str
# Creates plain-language summary

translate_text(text: str, target_language: Language) -> str
# Translates text to target language

answer_question(document_text, question, language) -> dict
# Answers questions about document
```

**Supported Document Types**:
- `rental_agreement`: Rental/lease agreements
- `affidavit`: Legal affidavits
- `will`: Wills and testaments

**Risk Levels**:
- 🔴 `HIGH`: Critical issues (automatic renewal, waiver of rights)
- 🟡 `MEDIUM`: Notable concerns (penalties, restrictions)
- 🟢 `LOW`: Minor clauses (optional provisions)

**Example**:
```python
from backend.services import ai_service
from backend.models.schemas import DocumentType, Language

# Generate rental agreement
draft = ai_service.draft_document(
    doc_type=DocumentType.RENTAL_AGREEMENT,
    data={
        "party_a": {"name": "Landlord", "address": "..."},
        "party_b": {"name": "Tenant", "address": "..."},
        "monthly_rent": 15000,
        ...
    },
    language=Language.EN
)

# Detect risks
risks = ai_service.detect_risks(draft)

# Get summary
summary = ai_service.summarize_document(draft, Language.EN)
```

---

### 3. Citation Service (`citation_service.py`)

**Purpose**: Extract and verify legal citations from documents

**Key Functions**:
```python
extract_citations_from_text(text: str) -> List[str]
# Finds potential citations in document

verify_citation(citation_text: str) -> Citation
# Verifies single citation against database

verify_all_citations(citations: List[str]) -> List[Citation]
# Batch verification of citations
```

**Citation Patterns Recognized**:
- Case citations: `AIR 1985 SC 800`
- Act references: `Indian Penal Code`
- Section references: `Section 123` or `S. 123`

**Data Model**:
```python
Citation(
    citation_text: str,      # e.g., "AIR 1985 SC 800"
    case_name: str,          # e.g., "Kesavananda Bharati v. State"
    year: int,               # e.g., 1985
    is_verified: bool,       # True if verified
    source: str              # Link to Indian Kanoon
)
```

**Integrated Legal Sources**:
- Indian Kanoon (https://www.indkanoon.org/)
- Supreme Court Cases (SCC)
- All India Reporter (AIR)
- Indian Law Reports (ILR)
- Bombay/Calcutta Law Reports

---

### 4. OCR Service (`ocr_service.py`)

**Purpose**: Extract text from documents (PDF, images, etc.)

**Key Functions**:
```python
extract_text_from_file(file_bytes: bytes, filename: str) -> Tuple[str, str]
# Extracts text and detects language
# Returns: (extracted_text, detected_language)
```

**Supported Formats**:
- 📄 PDF
- 🖼️ JPG, JPEG, PNG
- 📝 DOCX

**Language Detection**:
- Checks for Hindi Unicode characters (0x0900-0x097F)
- Returns `hi` for Hindi, `en` for English
- Heuristic: >10% Hindi chars = Hindi

**Example**:
```python
from backend.services import ocr_service

text, lang = ocr_service.extract_text_from_file(
    file_bytes=pdf_data,
    filename="agreement.pdf"
)
# text: "RENTAL AGREEMENT..."
# lang: "en"
```

---

### 5. Storage Service (`storage_service.py`)

**Purpose**: Persist and retrieve documents

**Key Functions**:
```python
save_created_document(doc: DocumentResult, mobile: str) -> str
# Saves generated document

save_scanned_document(doc: ScanDocumentResult, mobile: str) -> str
# Saves analyzed document

get_document(doc_id: str) -> Optional[object]
# Retrieves document by ID

list_user_documents(mobile: str) -> List[dict]
# Lists all user's documents

delete_document(doc_id: str, mobile: str) -> bool
# Deletes document

export_document(doc_id: str, format: str) -> Optional[str]
# Exports in JSON or TXT format
```

**Data Storage**:
```
_created_docs = {
    "doc_id_1": DocumentResult(...),
    "doc_id_2": DocumentResult(...),
}

_scanned_docs = {
    "doc_id_3": ScanDocumentResult(...),
}

_user_doc_index = {
    "9876543210": ["doc_id_1", "doc_id_2"],
    "9123456789": ["doc_id_3"],
}
```

**For Production**:
- Replace with PostgreSQL/MongoDB
- Use AWS S3 for document storage
- Implement document versioning
- Add full-text search capability

---

## Data Models

### User Models
```python
class User(BaseModel):
    id: str                          # Unique user ID
    mobile: str                      # 10-digit mobile
    name: str                        # Full name
    email: Optional[str]             # Optional email
    language: Language               # en or hi
    mode: InterfaceMode              # simple or advanced
    created_at: datetime             # Registration timestamp

class LoginResult(BaseModel):
    user: User                       # User object
    access_token: str                # Session token
```

### Document Models
```python
class DocumentResult(BaseModel):
    document_id: str                 # UUID
    document_type: DocumentType      # rental_agreement, affidavit, will
    content: str                     # Full document text
    summary: str                     # Plain-language summary
    summary_translated: Optional[str] # Hindi translation
    citations: List[Citation]        # Verified citations
    risk_clauses: List[RiskClause]  # Risk analysis
    overall_risk: RiskLevel          # High/Medium/Low
    created_at: datetime             # Creation time
    language: Language               # Output language

class ScanDocumentResult(BaseModel):
    document_id: str
    extracted_text: str              # OCR result
    detected_language: str           # Detected language
    summary: str
    summary_translated: Optional[str]
    citations: List[Citation]
    risk_clauses: List[RiskClause]
    overall_risk: RiskLevel
    scanned_at: datetime
```

---

## API Endpoints (if converted to REST API)

### Authentication
```
POST   /auth/register        # Register with OTP
POST   /auth/verify-otp      # Verify OTP and login
POST   /auth/logout          # Logout
GET    /auth/validate-token  # Validate session token
```

### Documents
```
POST   /documents/create     # Generate document
POST   /documents/scan       # Scan document
GET    /documents/{id}       # Get document
GET    /documents            # List user documents
DELETE /documents/{id}       # Delete document
GET    /documents/{id}/export # Export document
```

### Analysis
```
POST   /analysis/citations   # Extract citations
POST   /analysis/risks       # Detect risks
POST   /analysis/summary     # Summarize document
POST   /analysis/qa          # Answer question
```

---

## Configuration

### Environment Variables
```bash
# In .env file
DATABASE_URL=sqlite:///legal_saathi.db
OPENAI_API_KEY=sk-...
ENVIRONMENT=development
OTP_EXPIRY_SECONDS=300
```

### Settings
```python
# In config.py
class Config:
    DEBUG = True
    OTP_LENGTH = 6
    OTP_EXPIRY_SECONDS = 300
    TOKEN_EXPIRY_DAYS = 30
    SESSION_TIMEOUT_MINUTES = 30
```

---

## Security Considerations

### Current Implementation (Development)
- ✅ OTP-based authentication (no passwords)
- ✅ Session tokens for state management
- ✅ User data isolation

### Production Recommendations
- 🔒 Use HTTPS/TLS for all communication
- 🔒 Implement JWT tokens with expiration
- 🔒 Rate limiting on auth endpoints
- 🔒 Document encryption at rest
- 🔒 Audit logging for all actions
- 🔒 GDPR compliance for data storage
- 🔒 Role-based access control (RBAC)

---

## Performance Considerations

### Current Bottlenecks
- In-memory database (limited by RAM)
- Template-based generation (not real LLM)
- Synchronous processing

### Optimization Opportunities
- Implement caching for citations
- Use async/await for I/O operations
- Add document processing queue (Celery)
- Implement pagination for document lists
- Use CDN for static files

---

## Future Enhancements

### Phase 2 (Completed Phase 2A AI Core & Phase 2B RAG Pipeline)
- [x] Real LLM integration (OpenAI GPT-5.6)
- [x] RAG Vector Search & Embeddings (`text-embedding-3-small` + `DocumentChunkModel`)
- [x] Boundary-aware text chunker service
- [x] PostgreSQL & SQLite persistence
- [x] Grounded Legal Q&A & Hallucination Control
- [ ] Cloud storage (AWS S3)
- [ ] Email notifications
- [ ] Advanced search & filtering

### Phase 3
- [ ] Document collaboration
- [ ] E-signature integration
- [ ] Payment processing
- [ ] Analytics dashboard
- [ ] API for third-party developers

### Phase 4
- [ ] Mobile app (React Native/Flutter)
- [ ] Blockchain for document verification
- [ ] Lawyer marketplace integration
- [ ] Video consultation support
- [ ] Automated compliance checks

---

**System Designed & Documented for Scalability** 📈
