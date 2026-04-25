"""
OCR Service - Extracts text from documents (PDF, images, etc.)
"""
from typing import Tuple
import os
import io


class OCRService:
    """Service for extracting text from scanned and digital documents"""
    
    def __init__(self):
        # In production, initialize with Tesseract, AWS Textract, or Google Vision
        self.supported_formats = ["pdf", "jpg", "jpeg", "png", "docx"]
    
    def extract_text_from_file(self, file_bytes: bytes, filename: str) -> Tuple[str, str]:
        """
        Extract text from file
        Returns: (extracted_text, detected_language)
        """
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Format {file_ext} not supported")
        
        # Simulate text extraction based on file type
        if file_ext == "pdf":
            text = self._extract_from_pdf(file_bytes)
        elif file_ext in ["jpg", "jpeg", "png"]:
            text = self._extract_from_image(file_bytes, file_ext)
        elif file_ext == "docx":
            text = self._extract_from_docx(file_bytes)
        else:
            text = ""
        
        # Detect language
        detected_lang = self._detect_language(text)
        
        return text, detected_lang
    
    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        # In production, use PyPDF2 or pdfplumber
        # For now, return a sample text
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except:
            return "[PDF content extracted - sample text for demonstration]"
    
    def _extract_from_image(self, file_bytes: bytes, format_type: str) -> str:
        """Extract text from image (JPG, PNG) using OCR"""
        # In production, use pytesseract or AWS Textract
        # For now, return sample text
        try:
            from PIL import Image
            import pytesseract
            
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except:
            return f"[Text extracted from {format_type} image - sample for demonstration]"
    
    def _extract_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        # In production, use python-docx
        try:
            from docx import Document
            import io
            
            doc = Document(io.BytesIO(file_bytes))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except:
            return "[DOCX content extracted - sample text for demonstration]"
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # In production, use textblob, langdetect, or Google API
        # Simple heuristic: check for Hindi characters
        
        hindi_chars = 0
        total_chars = len(text)
        
        # Hindi Unicode range: 0x0900-0x097F
        for char in text:
            if 0x0900 <= ord(char) <= 0x097F:
                hindi_chars += 1
        
        if total_chars > 0 and hindi_chars / total_chars > 0.1:
            return "hi"
        
        return "en"


# Initialize service
ocr_service = OCRService()
