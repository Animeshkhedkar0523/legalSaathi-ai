"""
Database Configuration and Models
Supports SQLite for local development and PostgreSQL for production.
"""
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    Text,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

load_dotenv()

# Database URL - default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./legal_saathi.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model class
Base = declarative_base()


def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables automatically"""
    Base.metadata.create_all(bind=engine)


# ─── SQLAlchemy ORM Models ──────────────────────────────────────────────────────

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String(64), primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:12]}")
    mobile = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    language = Column(String(10), default="en")
    interface_mode = Column(String(20), default="simple")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("DocumentModel", back_populates="user", cascade="all, delete-orphan")


class DocumentModel(Base):
    __tablename__ = "documents"
    
    id = Column(String(64), primary_key=True, default=lambda: f"doc_{uuid.uuid4().hex[:12]}")
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=True)  # rental_agreement, affidavit, will, scanned
    doc_kind = Column(String(20), default="created")   # created vs scanned
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    summary_translated = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    overall_risk = Column(String(20), default="Low")
    risk_clauses_json = Column(JSON, nullable=True)
    document_status = Column(String(30), default="completed")  # created, scanned, draft, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="documents")
    citations = relationship("CitationModel", back_populates="document", cascade="all, delete-orphan")


class CitationModel(Base):
    __tablename__ = "citations"
    
    id = Column(String(64), primary_key=True, default=lambda: f"cite_{uuid.uuid4().hex[:12]}")
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    citation_text = Column(Text, nullable=False)
    case_name = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    source = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="citations")


class OTPModel(Base):
    __tablename__ = "otps"
    
    id = Column(String(64), primary_key=True, default=lambda: f"otp_{uuid.uuid4().hex[:12]}")
    mobile = Column(String(20), index=True, nullable=False)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    last_sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

