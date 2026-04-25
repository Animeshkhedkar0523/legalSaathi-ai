"""
Storage Service - Saves and retrieves documents from database
"""
import json
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import DocumentResult, ScanDocumentResult


# ── In-Memory Document Database ───────────────────────────────────────────────
_created_docs = {}      # {document_id: DocumentResult}
_scanned_docs = {}      # {document_id: ScanDocumentResult}
_user_doc_index = {}    # {mobile: [document_ids]}


class StorageService:
    """Service for storing and retrieving documents"""
    
    def save_created_document(self, doc: DocumentResult, mobile: str) -> str:
        """Save a created document"""
        doc_id = doc.document_id
        
        # Store document
        _created_docs[doc_id] = doc
        
        # Add to user index
        if mobile not in _user_doc_index:
            _user_doc_index[mobile] = []
        
        if doc_id not in _user_doc_index[mobile]:
            _user_doc_index[mobile].append(doc_id)
        
        return doc_id
    
    def save_scanned_document(self, doc: ScanDocumentResult, mobile: str) -> str:
        """Save a scanned document"""
        doc_id = doc.document_id
        
        # Store document
        _scanned_docs[doc_id] = doc
        
        # Add to user index
        if mobile not in _user_doc_index:
            _user_doc_index[mobile] = []
        
        if doc_id not in _user_doc_index[mobile]:
            _user_doc_index[mobile].append(doc_id)
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[object]:
        """Get a document by ID"""
        if doc_id in _created_docs:
            return _created_docs[doc_id]
        elif doc_id in _scanned_docs:
            return _scanned_docs[doc_id]
        return None
    
    def get_document_text(self, doc_id: str) -> Optional[str]:
        """Get document text/content by ID"""
        doc = self.get_document(doc_id)
        if doc:
            if hasattr(doc, 'content'):  # Created document
                return doc.content
            elif hasattr(doc, 'extracted_text'):  # Scanned document
                return doc.extracted_text
        return None
    
    def list_user_documents(self, mobile: str) -> List[dict]:
        """List all documents for a user"""
        doc_ids = _user_doc_index.get(mobile, [])
        documents = []
        
        for doc_id in doc_ids:
            doc = self.get_document(doc_id)
            if doc:
                doc_dict = doc.dict()
                doc_dict["title"] = (
                    f"{doc.document_type.value.replace('_', ' ').title()}" 
                    if hasattr(doc, 'document_type') 
                    else "Scanned Document"
                )
                documents.append(doc_dict)
        
        return sorted(documents, key=lambda x: x['created_at'] if 'created_at' in x else x['scanned_at'], reverse=True)
    
    def delete_document(self, doc_id: str, mobile: str) -> bool:
        """Delete a document"""
        if doc_id in _created_docs:
            del _created_docs[doc_id]
        elif doc_id in _scanned_docs:
            del _scanned_docs[doc_id]
        else:
            return False
        
        # Remove from user index
        if mobile in _user_doc_index and doc_id in _user_doc_index[mobile]:
            _user_doc_index[mobile].remove(doc_id)
        
        return True
    
    def update_document(self, doc_id: str, updates: dict) -> bool:
        """Update a document"""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        
        return True
    
    def export_document(self, doc_id: str, format: str = "json") -> Optional[str]:
        """Export document in different formats"""
        doc = self.get_document(doc_id)
        if not doc:
            return None
        
        if format == "json":
            return json.dumps(doc.dict(), default=str, indent=2)
        elif format == "txt":
            if hasattr(doc, 'content'):
                return doc.content
            elif hasattr(doc, 'extracted_text'):
                return doc.extracted_text
        
        return None


# Initialize service
storage_service = StorageService()
