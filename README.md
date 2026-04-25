# 🏛️ LegalSaathi – AI-Powered Legal Assistant

LegalSaathi is a cutting-edge legal document generation and analysis platform designed for India. It uses AI to help create, scan, analyze, and understand legal documents in plain language.

## ✨ Features

### 1. **Login & Registration with OTP**
- Mobile-based authentication
- OTP verification for secure login
- Support for multiple languages and interface modes

### 2. **Home Dashboard**
- Quick navigation to all features
- User profile management
- Language and interface mode preferences

### 3. **Create Legal Documents**
Supported document types:
- 📄 **Rental Agreement** (किराया समझौता)
- 📜 **Affidavit** (शपथ पत्र)
- 🖊️ **Will** (वसीयत)

AI generates customized documents based on user inputs with legal compliance.

### 4. **Scan Documents**
- Upload PDF, DOCX, JPG, or PNG files
- OCR-based text extraction
- Automatic language detection
- Document analysis without login (guest mode)

### 5. **Risk Analysis**
- Identifies high-risk, medium-risk, and low-risk clauses
- Provides actionable suggestions for each risky clause
- Overall risk assessment

### 6. **Citation Verification**
- Extracts legal citations from documents
- Verifies citations against Indian legal databases
- Links to Indian Kanoon for case references

### 7. **Document Summary**
- AI-generated plain-language summaries
- Bilingual support (English & Hindi)
- Key points extraction

### 8. **Q&A Feature**
- Ask questions about your documents
- Get answers with relevant clause references
- Document-aware responses

### 9. **Document History**
- View all created and scanned documents
- Access document metadata
- Risk level indicators

### 10. **Bilingual Support**
- English and Hindi interface
- Automatic document translation
- Localized content

## 📁 Project Structure

```
legal-doc-ai-vac/
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic models and enums
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py         # OTP & authentication
│   │   ├── ai_service.py           # Document generation & analysis
│   │   ├── citation_service.py     # Citation verification
│   │   ├── ocr_service.py          # Text extraction from documents
│   │   └── storage_service.py      # Document persistence
│   ├── utils/
│   │   └── __init__.py
│   ├── database/
│   │   └── __init__.py
│   └── __init__.py
├── streamlit_app/
│   └── app.py                       # Main Streamlit application
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Tesseract OCR (for image text extraction)

### Installation

1. **Clone or download the project**
   ```bash
   cd legal-doc-ai-vac
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract (for OCR)**
   - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - **Mac**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

### Running the Application

```bash
streamlit run streamlit_app/app.py
```

The app will open in your default browser at `http://localhost:8501`

## 🔐 Authentication Flow

1. User registers with mobile number and OTP
2. OTP sent via SMS (simulated in dev mode)
3. OTP verified and user logged in
4. Access token generated for session management

### Test Credentials (Development)
```
Mobile: 9876543210
OTP: Shown in UI (dev mode)
```

## 📄 Document Types

### Rental Agreement (किराया समझौता)
- Landlord and tenant details
- Property information
- Monthly rent and security deposit
- Lease duration
- Payment terms and conditions
- Dispute resolution clauses

### Affidavit (शपथ पत्र)
- Deponent declaration
- Subject of affidavit
- Factual statements
- Legal verification
- Notary requirements

### Will (वसीयत)
- Testator information
- Asset listing
- Distribution instructions
- Executor appointment
- Guardian nomination
- Witness requirements

## 🤖 AI Services

### Document Generation
- Template-based initial generation
- AI enhancement with verified legal citations
- Language-specific formatting

### Risk Detection
- Keyword-based clause analysis
- Risk level classification (Low/Medium/High)
- Actionable suggestions

### Summarization
- Key points extraction
- Plain-language conversion
- Bilingual output

### Q&A
- Document-aware question answering
- Relevant clause identification
- Citation references

## 🔗 Citation Database

Integrated with Indian legal sources:
- Indian Kanoon (https://www.indkanoon.org/)
- Indian Penal Code (IPC)
- Code of Civil Procedure (CPC)
- Indian Succession Act, 1925
- And 300+ other acts and cases

## 💾 Data Storage

Currently uses in-memory storage for:
- User profiles
- OTP verification
- Generated documents
- Scanned documents

### For Production:
- Replace with PostgreSQL/MongoDB
- Implement cloud storage (S3/GCS)
- Add document versioning
- Enable audit logging

## 🌐 Language Support

- **English** (en) - Complete support
- **Hindi** (hi) - Partial (translations available)

## 🛠️ Development Notes

### Services
Each service is modular and can be replaced:

```python
# Example: Using actual LLM instead of templates
from backend.services import ai_service
draft = ai_service.draft_document(
    doc_type=DocumentType.RENTAL_AGREEMENT,
    data=user_data,
    language=Language.EN
)
```

### Adding New Document Types
1. Add enum to `DocumentType` in `models/schemas.py`
2. Create template method in `ai_service.py`
3. Add form to `page_create_document()` in `app.py`

### Integrating Real LLM
Replace template generation with:
```python
import openai
response = openai.ChatCompletion.create(...)
```

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         Streamlit Frontend (Web UI)         │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│      Backend Services Layer                 │
├──────────────────────────────────────────────┤
│ • Auth Service     • AI Service              │
│ • Storage Service  • Citation Service       │
│ • OCR Service      • Utils                  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│     Data & External Services                │
├──────────────────────────────────────────────┤
│ • In-Memory DB    • Indian Kanoon API       │
│ • Document Store  • Tesseract OCR           │
│ • LLM (optional)  • SMS Gateway (optional)  │
└──────────────────────────────────────────────┘
```

## 🔒 Security Features

- OTP-based mobile authentication
- Session token management
- No password storage
- Secure document handling
- User data isolation

## 📱 Responsive Design

- Mobile-first design
- Touch-friendly buttons
- Voice-friendly interface (simple mode)
- Advanced mode for power users

## 🚦 Future Enhancements

- [ ] Integration with real LLM (GPT-4, Claude)
- [ ] Real SMS gateway integration
- [ ] PostgreSQL backend
- [ ] Cloud storage (AWS S3, Google Cloud)
- [ ] Document collaboration features
- [ ] E-signature support
- [ ] Payment processing
- [ ] Mobile app (React Native)
- [ ] API for third-party integration
- [ ] Advanced analytics dashboard

## 📞 Support

For issues or feature requests, please contact the development team.

## 📄 License

This project is proprietary and confidential. All rights reserved.

## ⚖️ Legal Disclaimer

**IMPORTANT:** LegalSaathi is an AI assistant for document generation and analysis. It is **NOT a substitute for professional legal advice**. 

- Always consult with a qualified lawyer before executing any legal document
- Documents generated should be reviewed and customized as per individual needs
- The platform provides general guidance, not legal counsel
- User assumes full responsibility for documents generated or analyzed

---

**Made with ❤️ for India's Legal System**
