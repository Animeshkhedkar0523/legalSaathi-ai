"""
Database Configuration and Models
In production, replace in-memory storage with actual database (PostgreSQL, MongoDB, etc.)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - use SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./legal_saathi.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()


def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Future: SQLAlchemy Models ──────────────────────────────────────────────────
# These are placeholders for future database implementation
# Uncomment and implement when moving from in-memory storage to actual database

"""
from sqlalchemy import Column, String, DateTime, JSON, Enum, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    mobile = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, nullable=True)
    language = Column(String, default="en")
    mode = Column(String, default="simple")
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("DocumentModel", back_populates="user")


class DocumentModel(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    doc_type = Column(String)  # created, scanned
    document_type = Column(String, nullable=True)  # rental_agreement, affidavit, will
    title = Column(String, nullable=True)
    content = Column(String)
    summary = Column(String, nullable=True)
    language = Column(String, default="en")
    risk_level = Column(String)  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    scanned_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="documents")
    citations = relationship("CitationModel", back_populates="document")


class CitationModel(Base):
    __tablename__ = "citations"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"))
    citation_text = Column(String)
    case_name = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    source = Column(String, nullable=True)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="citations")
"""
