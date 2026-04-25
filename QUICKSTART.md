# 🚀 Quick Start Guide - LegalSaathi

## Step 1: Installation

### On Windows:
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### On Mac/Linux:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Install Tesseract OCR (for document scanning)

### Windows:
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Note the installation path (usually `C:\Program Files\Tesseract-OCR`)
4. Set environment variable or update ocr_service.py

### Mac:
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr
```

## Step 3: Run the Application

```bash
streamlit run streamlit_app/app.py
```

The app will open at: **http://localhost:8501**

## Step 4: Test the Application

### Registration:
1. Click "New Registration" tab
2. Enter details:
   - **Name**: Your Name
   - **Mobile**: 9876543210 (10 digits)
   - **Language**: English or हिंदी
   - **Mode**: Simple or Advanced
3. Click "📲 Send OTP"
4. Copy the OTP shown on screen

### Login:
1. Click "Login / OTP" tab
2. Enter:
   - **Mobile**: 9876543210
   - **OTP**: Paste the OTP from registration
3. Click "✅ Verify & Login"

### Create Document:
1. Click "📝 Create Document"
2. Select document type (Rental Agreement)
3. Fill in details
4. Click "🤖 Generate Document"
5. View, download, or analyze the document

### Scan Document:
1. Click "📤 Scan Document"
2. Upload a PDF/JPG/PNG
3. Click "🔍 Analyse Document"
4. Get summary, risk analysis, and citations

### Ask Questions:
1. Create or scan a document first
2. Click "❓ Q&A"
3. Select a document
4. Ask a question about it
5. Get AI-powered answer with relevant clauses

## Features Overview

| Feature | Status | Details |
|---------|--------|---------|
| 🔐 OTP Authentication | ✅ Complete | Mobile-based login |
| 📝 Create Documents | ✅ Complete | 3 document types |
| 📤 Scan Documents | ✅ Complete | OCR-based extraction |
| 📚 Citation Verification | ✅ Complete | Links to Indian Kanoon |
| ⚠️ Risk Analysis | ✅ Complete | Clause risk detection |
| 📋 Document History | ✅ Complete | View all documents |
| 🌐 Bilingual Support | ✅ Complete | English + Hindi |
| ❓ Q&A Feature | ✅ Complete | Document-aware questions |

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Make sure you've installed all dependencies
```bash
pip install -r requirements.txt
```

### Issue: Streamlit port already in use
**Solution**: Run on different port
```bash
streamlit run streamlit_app/app.py --server.port 8502
```

### Issue: OCR not working
**Solution**: Install Tesseract (see Step 2 above)

### Issue: "OTP not found" error
**Solution**: Register first, then use the OTP from registration

## Project Structure Quick Reference

```
legal-doc-ai-vac/
├── backend/
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   │   ├── auth_service.py       ← OTP & login
│   │   ├── ai_service.py         ← Document generation
│   │   ├── ocr_service.py        ← Text extraction
│   │   ├── citation_service.py   ← Citation verification
│   │   └── storage_service.py    ← Document storage
│   └── utils/
├── streamlit_app/
│   └── app.py               # Main web app
├── config.py                # Configuration
└── requirements.txt         # Dependencies
```

## Configuration

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

Edit `.env` with your API keys and settings.

## Next Steps

1. ✅ Run the app
2. ✅ Test with sample documents
3. 📝 Customize document templates (in `ai_service.py`)
4. 🔗 Integrate real LLM (OpenAI, Anthropic, etc.)
5. 💾 Set up production database (PostgreSQL)
6. 📧 Configure SMS gateway (Twilio, AWS SNS)

## Common Tasks

### Add a New Document Type:
1. Add to `DocumentType` enum in `models/schemas.py`
2. Create template in `ai_service.py`
3. Add form in `page_create_document()` in `app.py`

### Change Document Template:
```python
# In backend/services/ai_service.py
def _rental_agreement_template(self, data: dict) -> str:
    # Modify HTML/text here
    return f"...modified template..."
```

### Enable Real LLM:
```python
# In backend/services/ai_service.py
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
# Use openai.ChatCompletion.create(...) instead of templates
```

## Support & Issues

- Check `README.md` for detailed documentation
- Review `config.py` for configuration options
- Check `.env.example` for all available settings

---

**Happy Legal Documenting! ⚖️**
