# 📚 LegalSaathi Backend API Documentation

## Overview

The LegalSaathi backend is a FastAPI application that provides REST endpoints for:
- User authentication (OTP-based)
- Legal document generation
- Document scanning and OCR
- Risk analysis and citation verification
- Q&A and document summarization
- Multi-language translation

## Base URL

```
http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Authentication

Most endpoints require authentication using a Bearer token.

### How to Authenticate

1. Register and get OTP → Get access token
2. Include token in Authorization header:
   ```
   Authorization: Bearer {access_token}
   ```

### Authentication Flow

```
Register → Send OTP → Verify OTP → Get Token → Use in Headers
```

---

## 🔐 Authentication Endpoints

### 1. Register User

**Endpoint**: `POST /auth/register`

Registers a new user and sends OTP to their mobile number.

**Request**:
```json
{
  "mobile": "9876543210",
  "name": "Raj Kumar",
  "email": "raj@example.com",
  "language": "en",
  "mode": "simple"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "OTP sent to 9876543210",
  "dev_otp": "123456"  // Only for development
}
```

---

### 2. Verify OTP & Login

**Endpoint**: `POST /auth/verify-otp`

Verifies the OTP and returns an access token.

**Request**:
```json
{
  "mobile": "9876543210",
  "otp": "123456"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "user": {
    "id": "user_1234567890_abcd",
    "mobile": "9876543210",
    "name": "Raj Kumar",
    "email": "raj@example.com",
    "language": "en",
    "mode": "simple"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 3. Get Current User

**Endpoint**: `GET /auth/me`

Get information about the logged-in user.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "id": "user_1234567890_abcd",
  "mobile": "9876543210",
  "name": "Raj Kumar",
  "email": "raj@example.com",
  "language": "en",
  "mode": "simple"
}
```

---

### 4. Logout

**Endpoint**: `POST /auth/logout`

Logout and invalidate the current token.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 📄 Document Generation Endpoints

### 1. Draft a Legal Document

**Endpoint**: `POST /documents/draft`

Generate a legal document (Rental Agreement, Affidavit, Will).

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "doc_type": "rental_agreement",
  "language": "en",
  "include_citations": true,
  "data": {
    "party_a": {
      "name": "Landlord Name",
      "address": "123 Main Street",
      "contact": "9876543210"
    },
    "party_b": {
      "name": "Tenant Name",
      "address": "456 Oak Avenue",
      "contact": "9876543211"
    },
    "property_address": "789 Park Road, Bangalore",
    "monthly_rent": 25000,
    "security_deposit": 75000,
    "duration_months": 12,
    "start_date": "2026-02-01"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "content": "RENTAL AGREEMENT\n\nThis Rental Agreement...",
  "summary": "This document is a legal agreement containing...",
  "citations": [
    {
      "citation_text": "Transfer of Property Act",
      "case_name": "Transfer of Property Act, 1882",
      "year": 1882,
      "is_verified": true,
      "source": "https://www.indkanoon.org/..."
    }
  ],
  "risk_analysis": {
    "clauses": [
      {
        "clause_text": "Clause containing 'automatic renewal'",
        "risk_level": "High",
        "risk_reason": "This clause involves 'automatic renewal' which may have legal implications.",
        "suggestion": "Review and clarify the 'automatic renewal' clause carefully."
      }
    ],
    "overall_risk": "High"
  }
}
```

**Document Types**:
- `rental_agreement` - Rental/Lease agreement
- `affidavit` - Affidavit/Statutory declaration
- `will` - Will/Testament

---

## 📋 Document Scanning Endpoints

### 1. Scan and Analyze Document

**Endpoint**: `POST /documents/scan`

Upload and analyze a document file (PDF, Image, DOCX).

**Note**: No authentication required (guest mode)

**Request** (multipart/form-data):
```
file: <binary file>
title: "My Legal Document" (optional)
language: "en" (optional)
```

**Supported Formats**:
- PDF
- JPG / JPEG
- PNG
- DOCX

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "scan_x1y2z3a4b5c6",
  "extracted_text": "Text extracted from the document...",
  "detected_language": "en",
  "summary": "This document is a legal agreement...",
  "citations": [...],
  "risk_analysis": {...}
}
```

---

## 📚 Document Retrieval Endpoints

### 1. List User Documents

**Endpoint**: `GET /documents`

Get all documents for the current user.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "count": 3,
  "documents": [
    {
      "document_id": "doc_a1b2c3d4e5f6",
      "document_type": "rental_agreement",
      "title": "Rental Agreement",
      "created_at": "2026-02-01T10:30:00",
      "overall_risk": "High"
    }
  ]
}
```

---

### 2. Get Specific Document

**Endpoint**: `GET /documents/{document_id}`

Retrieve a specific document by ID.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "document": {
    "document_id": "doc_a1b2c3d4e5f6",
    "document_type": "rental_agreement",
    "content": "RENTAL AGREEMENT...",
    "summary": "This document is...",
    "citations": [...],
    "risk_clauses": [...],
    "overall_risk": "High",
    "created_at": "2026-02-01T10:30:00",
    "language": "en",
    "title": "Rental Agreement"
  }
}
```

---

### 3. Delete Document

**Endpoint**: `DELETE /documents/{document_id}`

Delete a document.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Document deleted"
}
```

---

## 🔍 Document Analysis Endpoints

### 1. Analyze Risks

**Endpoint**: `POST /documents/{document_id}/risk-analysis`

Perform detailed risk analysis on a document.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "risk_clauses": [
    {
      "clause_text": "Clause containing 'automatic renewal'",
      "risk_level": "High",
      "risk_reason": "This clause involves automatic renewal which may have legal implications.",
      "suggestion": "Review and clarify the clause carefully."
    }
  ],
  "overall_risk": "High"
}
```

**Risk Levels**:
- `Low` - Minimal legal risk
- `Medium` - Moderate risk, review recommended
- `High` - Significant risk, professional consultation recommended

---

### 2. Get Document Summary

**Endpoint**: `POST /documents/{document_id}/summarize`

Get a plain-language summary of the document.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
```
language: "en" or "hi" (optional, default: en)
```

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "summary": "This document is a legal agreement containing the following key points...",
  "summary_translated": "[हिंदी अनुवाद] यह दस्तावेज़ एक कानूनी समझौता है..."
}
```

---

## 📖 Citations Endpoints

### 1. Extract and Verify Citations

**Endpoint**: `POST /documents/{document_id}/citations`

Extract legal citations and verify them against known databases.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "count": 3,
  "citations": [
    {
      "citation_text": "Transfer of Property Act",
      "case_name": "Transfer of Property Act, 1882",
      "year": 1882,
      "is_verified": true,
      "source": "https://www.indkanoon.org/doc/2067...",
      "verified": true
    },
    {
      "citation_text": "Section 123",
      "case_name": null,
      "year": null,
      "is_verified": false,
      "source": null
    }
  ]
}
```

---

## 💬 Q&A Endpoints

### 1. Ask Question About Document

**Endpoint**: `POST /documents/{document_id}/qa`

Ask natural language questions about a document and get relevant answers.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request**:
```json
{
  "question": "What are the tenant's payment obligations?",
  "language": "en"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "question": "What are the tenant's payment obligations?",
  "answer": "Based on the document: What are the tenant's payment obligations?. This depends on the specific terms outlined in the agreement. Please review the relevant clauses mentioned below carefully.",
  "relevant_clauses": [
    "Tenant shall bear the cost of electricity, water, and internet.",
    "Late payments shall incur an interest of 2% per month...",
    "Rent of ₹25000 shall be paid monthly on or before the 5th of each month."
  ],
  "confidence": 0.7
}
```

---

## 🌐 Translation Endpoints

### 1. Translate Document

**Endpoint**: `POST /documents/{document_id}/translate`

Translate a document to another language.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
```
target_language: "hi" (hindi) or "en" (english)
```

**Response** (200 OK):
```json
{
  "success": true,
  "document_id": "doc_a1b2c3d4e5f6",
  "original_language": "en",
  "target_language": "hi",
  "translated_content": "[हिंदी अनुवाद - Hindi Translation]...",
  "note": "For accurate legal translation, consult a professional translator"
}
```

---

## 🏥 Health Check

### System Health Status

**Endpoint**: `GET /health`

Check if the API is running.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "LegalSaathi API",
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": "Description of the error",
  "timestamp": "2026-02-01T10:30:00.123456"
}
```

### Common Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request / Validation error |
| 401 | Unauthorized / Invalid token |
| 404 | Not found |
| 500 | Server error |

---

## Code Examples

### Python (Requests)

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "mobile": "9876543210",
        "name": "Raj Kumar",
        "email": "raj@example.com",
        "language": "en",
        "mode": "simple"
    }
)
print(response.json())

# 2. Verify OTP
response = requests.post(
    f"{BASE_URL}/auth/verify-otp",
    json={
        "mobile": "9876543210",
        "otp": "123456"
    }
)
token = response.json()["access_token"]

# 3. Draft Document
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/documents/draft",
    headers=headers,
    json={
        "doc_type": "rental_agreement",
        "language": "en",
        "include_citations": True,
        "data": {...}
    }
)
print(response.json())
```

### JavaScript/TypeScript

```javascript
const BASE_URL = "http://localhost:8000";

// 1. Register
const registerRes = await fetch(`${BASE_URL}/auth/register`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mobile: "9876543210",
    name: "Raj Kumar",
    email: "raj@example.com",
    language: "en",
    mode: "simple"
  })
});
const registerData = await registerRes.json();

// 2. Verify OTP
const verifyRes = await fetch(`${BASE_URL}/auth/verify-otp`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mobile: "9876543210",
    otp: "123456"
  })
});
const verifyData = await verifyRes.json();
const token = verifyData.access_token;

// 3. Draft Document
const draftRes = await fetch(`${BASE_URL}/documents/draft`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  },
  body: JSON.stringify({
    doc_type: "rental_agreement",
    language: "en",
    include_citations: true,
    data: { /* ... */ }
  })
});
const draftData = await draftRes.json();
```

---

## Rate Limiting

Currently, there is no rate limiting. In production, implement:
- 100 requests per minute per user
- 1000 requests per hour per IP

---

## CORS

CORS is enabled for all origins (`*`) in development mode. In production, restrict to:
```
["https://yourdomain.com", "https://app.yourdomain.com"]
```

---

## Support & Contact

For issues, questions, or feedback, contact:
- Email: support@legalsaathi.com
- GitHub: https://github.com/yourusername/legal-doc-ai-vac
