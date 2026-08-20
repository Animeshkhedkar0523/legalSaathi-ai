"""
Storage Service - Saves and retrieves documents using SQLAlchemy Database
"""
import json
from typing import List, Optional, Union
from datetime import datetime
from backend.database import SessionLocal, UserModel, DocumentModel, CitationModel
from backend.models.schemas import (
    DocumentResult,
    ScanDocumentResult,
    DocumentType,
    Language,
    RiskLevel,
    Citation,
    RiskClause
)


class StorageService:
    """Service for storing and retrieving documents from the database"""
    
    def _get_or_create_user(self, session, mobile: str) -> UserModel:
        """Helper to find user by mobile or create guest user if missing"""
        user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
        if not user:
            user = UserModel(
                mobile=mobile,
                name="Guest User",
                language="en",
                interface_mode="simple",
                is_verified=False
            )
            session.add(user)
            session.flush()
        return user

    def save_created_document(self, doc: DocumentResult, mobile: str) -> str:
        """Save a created document to database"""
        session = SessionLocal()
        try:
            user = self._get_or_create_user(session, mobile)
            
            doc_type_val = doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type)
            lang_val = doc.language.value if hasattr(doc.language, 'value') else str(doc.language)
            risk_val = doc.overall_risk.value if hasattr(doc.overall_risk, 'value') else str(doc.overall_risk)
            
            risk_clauses_data = []
            if doc.risk_clauses:
                for rc in doc.risk_clauses:
                    if hasattr(rc, 'dict'):
                        risk_clauses_data.append(rc.dict())
                    elif isinstance(rc, dict):
                        risk_clauses_data.append(rc)
            
            db_doc = DocumentModel(
                id=doc.document_id,
                user_id=user.id,
                document_type=doc_type_val,
                doc_kind="created",
                title=getattr(doc, 'title', None) or f"{doc_type_val.replace('_', ' ').title()}",
                content=doc.content,
                summary=doc.summary,
                summary_translated=getattr(doc, 'summary_translated', None),
                language=lang_val,
                overall_risk=risk_val,
                risk_clauses_json=risk_clauses_data,
                document_status="completed",
                created_at=doc.created_at if hasattr(doc, 'created_at') and doc.created_at else datetime.utcnow()
            )
            session.add(db_doc)
            
            if doc.citations:
                for c in doc.citations:
                    cite_text = c.citation_text if hasattr(c, 'citation_text') else c.get('citation_text', '')
                    c_model = CitationModel(
                        document_id=doc.document_id,
                        citation_text=cite_text,
                        case_name=c.case_name if hasattr(c, 'case_name') else c.get('case_name'),
                        year=c.year if hasattr(c, 'year') else c.get('year'),
                        is_verified=c.is_verified if hasattr(c, 'is_verified') else c.get('is_verified', False),
                        source=c.source if hasattr(c, 'source') else c.get('source')
                    )
                    session.add(c_model)
            
            session.commit()
            return doc.document_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_scanned_document(self, doc: ScanDocumentResult, mobile: str) -> str:
        """Save a scanned document to database"""
        session = SessionLocal()
        try:
            user = self._get_or_create_user(session, mobile)
            
            risk_val = doc.overall_risk.value if hasattr(doc.overall_risk, 'value') else str(doc.overall_risk)
            
            risk_clauses_data = []
            if doc.risk_clauses:
                for rc in doc.risk_clauses:
                    if hasattr(rc, 'dict'):
                        risk_clauses_data.append(rc.dict())
                    elif isinstance(rc, dict):
                        risk_clauses_data.append(rc)
            
            db_doc = DocumentModel(
                id=doc.document_id,
                user_id=user.id,
                document_type="scanned",
                doc_kind="scanned",
                title=getattr(doc, 'title', None) or "Scanned Document",
                content=doc.extracted_text,
                summary=doc.summary,
                summary_translated=getattr(doc, 'summary_translated', None),
                language=getattr(doc, 'detected_language', 'en'),
                overall_risk=risk_val,
                risk_clauses_json=risk_clauses_data,
                document_status="scanned",
                created_at=doc.scanned_at if hasattr(doc, 'scanned_at') and doc.scanned_at else datetime.utcnow()
            )
            session.add(db_doc)
            
            if doc.citations:
                for c in doc.citations:
                    cite_text = c.citation_text if hasattr(c, 'citation_text') else c.get('citation_text', '')
                    c_model = CitationModel(
                        document_id=doc.document_id,
                        citation_text=cite_text,
                        case_name=c.case_name if hasattr(c, 'case_name') else c.get('case_name'),
                        year=c.year if hasattr(c, 'year') else c.get('year'),
                        is_verified=c.is_verified if hasattr(c, 'is_verified') else c.get('is_verified', False),
                        source=c.source if hasattr(c, 'source') else c.get('source')
                    )
                    session.add(c_model)
            
            session.commit()
            return doc.document_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_document(self, doc_id: str) -> Optional[Union[DocumentResult, ScanDocumentResult]]:
        """Get a document by ID and convert to schema object"""
        session = SessionLocal()
        try:
            db_doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not db_doc:
                return None
            
            citations = []
            for c in db_doc.citations:
                citations.append(Citation(
                    citation_text=c.citation_text,
                    case_name=c.case_name,
                    year=c.year,
                    is_verified=c.is_verified,
                    source=c.source
                ))
            
            risk_clauses = []
            if db_doc.risk_clauses_json:
                for rc_data in db_doc.risk_clauses_json:
                    risk_lvl = rc_data.get('risk_level', 'Low')
                    try:
                        risk_lvl_enum = RiskLevel(risk_lvl)
                    except ValueError:
                        risk_lvl_enum = RiskLevel.LOW
                        
                    risk_clauses.append(RiskClause(
                        clause_text=rc_data.get('clause_text', ''),
                        risk_level=risk_lvl_enum,
                        risk_reason=rc_data.get('risk_reason', ''),
                        suggestion=rc_data.get('suggestion')
                    ))
            
            try:
                overall_risk_enum = RiskLevel(db_doc.overall_risk)
            except ValueError:
                overall_risk_enum = RiskLevel.LOW

            if db_doc.doc_kind == "scanned":
                return ScanDocumentResult(
                    document_id=db_doc.id,
                    extracted_text=db_doc.content,
                    detected_language=db_doc.language or "en",
                    summary=db_doc.summary or "",
                    summary_translated=db_doc.summary_translated,
                    citations=citations,
                    risk_clauses=risk_clauses,
                    overall_risk=overall_risk_enum,
                    scanned_at=db_doc.created_at,
                    title=db_doc.title
                )
            else:
                try:
                    doc_type_enum = DocumentType(db_doc.document_type)
                except ValueError:
                    doc_type_enum = DocumentType.RENTAL_AGREEMENT
                
                try:
                    lang_enum = Language(db_doc.language)
                except ValueError:
                    lang_enum = Language.EN

                return DocumentResult(
                    document_id=db_doc.id,
                    document_type=doc_type_enum,
                    content=db_doc.content,
                    summary=db_doc.summary or "",
                    summary_translated=db_doc.summary_translated,
                    citations=citations,
                    risk_clauses=risk_clauses,
                    overall_risk=overall_risk_enum,
                    created_at=db_doc.created_at,
                    language=lang_enum,
                    title=db_doc.title
                )
        finally:
            session.close()
    
    def get_document_text(self, doc_id: str) -> Optional[str]:
        """Get document text/content by ID"""
        session = SessionLocal()
        try:
            db_doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            return db_doc.content if db_doc else None
        finally:
            session.close()
    
    def list_user_documents(self, mobile: str) -> List[dict]:
        """List all documents for a user"""
        session = SessionLocal()
        try:
            user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
            if not user:
                return []
            
            docs = (
                session.query(DocumentModel)
                .filter(DocumentModel.user_id == user.id)
                .order_by(DocumentModel.created_at.desc())
                .all()
            )
            
            results = []
            for d in docs:
                title = d.title or (
                    d.document_type.replace('_', ' ').title() if d.document_type else "Document"
                )
                results.append({
                    "document_id": d.id,
                    "title": title,
                    "document_type": d.document_type,
                    "doc_kind": d.doc_kind,
                    "language": d.language,
                    "overall_risk": {"value": d.overall_risk},
                    "summary": d.summary,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "scanned_at": d.created_at.isoformat() if d.created_at else None,
                })
            return results
        finally:
            session.close()

    def get_user_document_by_id(self, doc_id: str, user_id: str) -> Optional[DocumentModel]:
        """Get document by ID ensuring user ownership"""
        session = SessionLocal()
        try:
            return session.query(DocumentModel).filter(
                DocumentModel.id == doc_id,
                DocumentModel.user_id == user_id
            ).first()
        finally:
            session.close()

    def delete_document(self, doc_id: str, mobile: str = None, user_id: str = None) -> bool:
        """Delete a document by ID with optional mobile/user_id ownership check"""
        session = SessionLocal()
        try:
            query = session.query(DocumentModel).filter(DocumentModel.id == doc_id)
            if user_id:
                query = query.filter(DocumentModel.user_id == user_id)
            elif mobile:
                user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
                if user:
                    query = query.filter(DocumentModel.user_id == user.id)
                else:
                    return False

            doc = query.first()
            if not doc:
                return False
            
            session.delete(doc)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_document(self, doc_id: str, updates: dict) -> bool:
        """Update a document in database"""
        session = SessionLocal()
        try:
            doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not doc:
                return False
            
            for key, value in updates.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)
            
            doc.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
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


# Initialize service instance
storage_service = StorageService()
