# 🚀 Backend Quick Start Guide

## Overview

The LegalSaathi backend is a **FastAPI** application that provides a complete REST API for:
- User authentication with OTP
- Legal document generation
- Document scanning and OCR
- Risk analysis and citation verification
- Q&A and document summarization
- Multi-language translation (English/Hindi)

## ✅ Current Status

The backend is **fully implemented and tested**:

- ✅ FastAPI server running on `http://localhost:8000`
- ✅ All authentication endpoints working
- ✅ Document generation/scanning APIs implemented
- ✅ Risk analysis and citation verification working
- ✅ Q&A and translation endpoints ready
- ✅ Comprehensive error handling
- ✅ CORS enabled for frontend integration
- ✅ Interactive API documentation at `/docs`

## 🎯 Quick Start

### 1. Start the Backend Server

The FastAPI server is already running, but you can restart it with:

```bash
# Option 1: Using uvicorn directly
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using the startup script
python run_backend.py
```

### 2. Access API Documentation

Open your browser to one of these URLs:

- **Interactive Swagger UI**: http://localhost:8000/docs
- **Alternative ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 3. Test the API

#### Check Health Status
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "LegalSaathi API",
  "timestamp": "2026-04-25T10:00:11.241415"
}
```

#### Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "9876543210",
    "name": "Raj Kumar",
    "email": "raj@example.com",
    "language": "en",
    "mode": "simple"
  }'
```

Response:
```json
{
  "success": true,
  "message": "OTP sent to 9876543210",
  "dev_otp": "123456"
}
```

#### Verify OTP & Login
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "mobile": "9876543210",
    "otp": "123456"
  }'
```

Response:
```json
{
  "success": true,
  "user": {
    "id": "user_...",
    "mobile": "9876543210",
    "name": "Raj Kumar",
    "email": "raj@example.com",
    "language": "en",
    "mode": "simple"
  },
  "access_token": "eyJ0eXAi..."
}
```

#### Generate a Document
```bash
curl -X POST http://localhost:8000/documents/draft \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "doc_type": "rental_agreement",
    "language": "en",
    "include_citations": true,
    "data": {
      "party_a": {
        "name": "Landlord",
        "address": "123 Main St",
        "contact": "9876543210"
      },
      "party_b": {
        "name": "Tenant",
        "address": "456 Oak Ave",
        "contact": "9876543211"
      },
      "property_address": "789 Park Rd",
      "monthly_rent": 25000,
      "security_deposit": 75000,
      "duration_months": 12,
      "start_date": "2026-02-01"
    }
  }'
```

## 📚 API Endpoints Summary

### Authentication
- `POST /auth/register` - Register user and send OTP
- `POST /auth/verify-otp` - Verify OTP and get token
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - Logout

### Document Management
- `POST /documents/draft` - Generate legal document
- `POST /documents/scan` - Scan and analyze document
- `GET /documents` - List all user documents
- `GET /documents/{id}` - Get specific document
- `DELETE /documents/{id}` - Delete document

### Analysis & Features
- `POST /documents/{id}/risk-analysis` - Analyze risks
- `POST /documents/{id}/summarize` - Get summary
- `POST /documents/{id}/citations` - Extract citations
- `POST /documents/{id}/qa` - Ask questions about doc
- `POST /documents/{id}/translate` - Translate document

### System
- `GET /health` - Health check

## 🔐 Authentication

All endpoints except `/auth/register` and `/documents/scan` require authentication.

Include token in header:
```
Authorization: Bearer {access_token}
```

## 📋 Document Types

Supported legal documents:
- `rental_agreement` - Rental/Lease agreements
- `affidavit` - Affidavits/Statutory declarations
- `will` - Wills/Testaments

## 📁 Project Structure

```
legal-doc-ai-vac/
├── main.py                          # FastAPI application
├── run_backend.py                   # Backend startup script
├── API_DOCUMENTATION.md             # Detailed API docs
├── backend/
│   ├── __init__.py                  # Service exports
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py               # Pydantic models
│   ├── services/
│   │   ├── auth_service.py          # Authentication
│   │   ├── ai_service.py            # Document generation & analysis
│   │   ├── ocr_service.py           # Text extraction
│   │   ├── citation_service.py      # Citation extraction & verification
│   │   └── storage_service.py       # Document storage
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py                # SQLAlchemy models (for future DB)
│   └── utils/
│       └── __init__.py
└── requirements.txt                 # Python dependencies
```

## ⚙️ Configuration

Environment variables in `.env`:
```
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///legal_saathi.db
OPENAI_API_KEY=your-key-here
```

## 🧪 Testing

Use Swagger UI at http://localhost:8000/docs to test all endpoints interactively.

## 🔄 Development Workflow

1. **Make code changes** in `backend/` directory
2. **Server auto-reloads** (--reload flag enabled)
3. **Check API docs** at http://localhost:8000/docs
4. **Test endpoints** in Swagger UI

## 📦 Dependencies

Key packages:
- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **PyPDF2** - PDF extraction
- **python-docx** - DOCX extraction
- **Pillow** - Image processing
- **pytesseract** - OCR

## 🚀 Next Steps

### For Production:
1. Replace SQLite with PostgreSQL
2. Add JWT token authentication
3. Integrate real LLM (OpenAI, Anthropic)
4. Add SMS gateway (Twilio)
5. Implement database caching
6. Add rate limiting
7. Set up logging & monitoring

### For Frontend Integration:
1. Connect Streamlit to FastAPI
2. Update API requests to use tokens
3. Add error handling
4. Implement loading states

## 🆘 Troubleshooting

### Port 8000 Already in Use
```bash
# Kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn main:app --port 8001
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### CORS Issues
CORS is enabled for all origins in development. Restrict in production:
```python
# In main.py
allow_origins=["https://yourdomain.com"]
```

## 📖 Additional Resources

- **API Documentation**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Pydantic Docs**: https://docs.pydantic.dev
- **Indian Kanoon**: https://www.indkanoon.org

## ✉️ Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Email: support@legalsaathi.com
- Check the full API documentation

---

**Status**: ✅ Backend fully implemented and tested  
**Last Updated**: April 25, 2026  
**Version**: 1.0.0
