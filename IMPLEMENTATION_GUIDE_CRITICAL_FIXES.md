# 🚀 LEGALSAATHI - IMPLEMENTATION GUIDE FOR CRITICAL FIXES

**Priority**: 🔴 **MUST DO IN NEXT 2 WEEKS**  
**Target**: Get from Prototype to MVP-Ready

---

## PART 1: DATABASE MIGRATION (2-3 Days)

### Step 1.1: Install PostgreSQL and Create Database

```bash
# On Windows
# Download from: https://www.postgresql.org/download/windows/
# Or use WSL: wsl -d Ubuntu -u root apt-get install postgresql

# On Linux/Mac
brew install postgresql@15

# Start PostgreSQL service
pg_ctl -D /usr/local/var/postgres start

# Create database
createdb legalsaathi
createuser legalsaathi_user
psql -d postgres -c "ALTER USER legalsaathi_user WITH PASSWORD 'secure_password_here';"
```

### Step 1.2: Update requirements.txt

```txt
# Add these lines
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.13.0
python-dotenv>=1.0.0
```

### Step 1.3: Create .env file

```bash
# Create file: .env

DATABASE_URL=postgresql://legalsaathi_user:secure_password_here@localhost:5432/legalsaathi
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key-change-in-production-use-uuid-or-random-string
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
ENVIRONMENT=development
DEBUG=True
```

### Step 1.4: Create SQLAlchemy Models

Create file: `backend/database/models.py`

```python
"""
SQLAlchemy models for LegalSaathi
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    mobile = Column(String(20), unique=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True, nullable=True)
    language = Column(String(10), default="en")
    mode = Column(String(20), default="simple")
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, mobile={self.mobile}, name={self.name})>"


class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True)
    mobile = Column(String(20), ForeignKey("users.mobile"), index=True)
    otp_hash = Column(String(255))
    expires_at = Column(DateTime, index=True)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(255), nullable=True)
    doc_type = Column(String(50), index=True)  # rental_agreement, affidavit, will
    content = Column(Text)
    summary = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    overall_risk = Column(String(20), index=True)  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    risk_clauses = relationship("RiskClause", back_populates="document", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, type={self.doc_type}, risk={self.overall_risk})>"


class RiskClause(Base):
    __tablename__ = "risk_clauses"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    clause_text = Column(Text)
    risk_level = Column(String(20), index=True)  # LOW, MEDIUM, HIGH
    risk_reason = Column(Text)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="risk_clauses")


class Citation(Base):
    __tablename__ = "citations"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    citation_text = Column(String(500))
    case_name = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False, index=True)
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="citations")


class Lawyer(Base):
    __tablename__ = "lawyers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    mobile = Column(String(20), unique=True, index=True)
    specialization = Column(String(255), index=True)
    bio = Column(Text, nullable=True)
    verified = Column(Boolean, default=False, index=True)
    rating = Column(Float, default=0.0, index=True)
    reviews_count = Column(Integer, default=0)
    hourly_rate = Column(Integer)  # In paisa (100 paisa = 1 rupee)
    available_hours = Column(JSON)  # {"monday": ["09:00-17:00"], ...}
    languages = Column(JSON)  # ["en", "hi", "ta"]
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    plan = Column(String(50))  # basic, pro, enterprise
    status = Column(String(20), index=True)  # active, paused, cancelled
    razorpay_subscription_id = Column(String(255), unique=True, index=True)
    amount = Column(Integer)  # In paisa
    interval = Column(String(20), default="monthly")
    started_at = Column(DateTime, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
```

### Step 1.5: Create Database Connection

Create file: `backend/database/connection.py`

```python
"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from backend.database.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://legalsaathi_user:secure_password_here@localhost:5432/legalsaathi"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    echo=False,  # Set to True for SQL query logging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to inject database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 1.6: Migrate Old Data (One-Time)

Create file: `scripts/migrate_data.py`

```python
"""
Migrate data from in-memory to PostgreSQL
"""
import sys
sys.path.insert(0, '/path/to/project')

from backend.database.connection import SessionLocal, engine
from backend.database.models import User as DBUser, Document as DBDocument
from backend.services.auth_service import _USERS_DB, _DOCUMENTS_DB
from datetime import datetime

def migrate():
    """Migrate data from in-memory to PostgreSQL"""
    
    db = SessionLocal()
    
    # Migrate users
    print(f"Migrating {len(_USERS_DB)} users...")
    for mobile, user_data in _USERS_DB.items():
        db_user = DBUser(
            user_id=user_data.get('id'),
            mobile=mobile,
            name=user_data.get('name'),
            email=user_data.get('email'),
            language=user_data.get('language', 'en'),
            mode=user_data.get('mode', 'simple'),
            verified=user_data.get('verified', False),
            verified_at=datetime.fromisoformat(user_data['verified_at']) if user_data.get('verified_at') else None,
            created_at=datetime.fromisoformat(user_data['created_at'])
        )
        db.add(db_user)
    
    db.commit()
    print("✅ Users migrated successfully!")
    
    # Migrate documents
    print(f"Migrating {len(_DOCUMENTS_DB)} documents...")
    for doc_id, doc_data in _DOCUMENTS_DB.items():
        # Find corresponding user
        user = db.query(DBUser).filter_by(user_id=doc_data.get('user_id')).first()
        if not user:
            print(f"⚠️ User not found for document {doc_id}, skipping...")
            continue
        
        db_doc = DBDocument(
            id=doc_id,
            user_id=user.id,
            title=doc_data.get('title'),
            doc_type=doc_data.get('type'),
            content=doc_data.get('content'),
            summary=doc_data.get('summary'),
            language=doc_data.get('language', 'en'),
            overall_risk=doc_data.get('overall_risk'),
            created_at=datetime.fromisoformat(doc_data['created_at'])
        )
        db.add(db_doc)
    
    db.commit()
    print("✅ Documents migrated successfully!")
    db.close()

if __name__ == "__main__":
    migrate()
```

---

## PART 2: JWT AUTHENTICATION (2-3 Days)

### Step 2.1: Update requirements.txt

```txt
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

### Step 2.2: Create Authentication Manager

Replace: `backend/jwt_manager.py`

```python
"""
JWT Authentication Manager - Production Grade
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Header
import hashlib
import secrets

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in environment variables!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTManager:
    """JWT token management with security best practices"""
    
    # Token blacklist (in production, use Redis)
    _token_blacklist = set()
    
    @staticmethod
    def create_tokens(user_id: str, mobile: str) -> Dict[str, str]:
        """Create access and refresh tokens"""
        
        # Generate unique token IDs for revocation
        access_jti = secrets.token_urlsafe(32)
        refresh_jti = secrets.token_urlsafe(32)
        
        # Create access token
        access_payload = {
            "sub": user_id,
            "mobile": mobile,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.now(timezone.utc),
            "jti": access_jti
        }
        
        # Create refresh token
        refresh_payload = {
            "sub": user_id,
            "mobile": mobile,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc),
            "jti": refresh_jti
        }
        
        access_token = jwt.encode(
            access_payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }
    
    @staticmethod
    def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != expected_type:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token type. Expected {expected_type}, got {payload.get('type')}"
                )
            
            # Check if token is blacklisted (revoked)
            if payload.get("jti") in JWTManager._token_blacklist:
                raise HTTPException(
                    status_code=401,
                    detail="Token has been revoked"
                )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    @staticmethod
    def revoke_token(token: str):
        """Revoke a token (add to blacklist)"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            JWTManager._token_blacklist.add(payload.get("jti"))
            return True
        except:
            return False


# FastAPI dependency for authentication
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency to verify JWT token and extract user info"""
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization scheme. Use 'Bearer {token}'"
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    payload = JWTManager.verify_token(token, expected_type="access")
    
    user_id = payload.get("sub")
    mobile = payload.get("mobile")
    
    if not user_id or not mobile:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )
    
    return {
        "user_id": user_id,
        "mobile": mobile,
        "token_jti": payload.get("jti")
    }
```

### Step 2.3: Update Auth Service

Replace: `backend/services/auth_service.py`

```python
"""
Authentication Service - Production Grade with JWT
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from backend.models.schemas import User, UserRegister, LoginResult, Language, InterfaceMode
from backend.jwt_manager import JWTManager
from backend.database.connection import SessionLocal
from backend.database.models import User as DBUser, OTP as DBOTP
import hashlib
import os

# In production, use Twilio, AWS SNS, etc.
from backend.sms_gateway import sms_gateway


def _generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def _hash_otp(otp: str) -> str:
    """Hash OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()


def register_and_send_otp(data: UserRegister) -> dict:
    """Register user and send OTP"""
    
    db = SessionLocal()
    
    try:
        mobile = data.mobile
        
        # Check if user already exists
        user = db.query(DBUser).filter_by(mobile=mobile).first()
        
        if not user:
            # Create new user
            user = DBUser(
                mobile=mobile,
                name=data.name,
                email=data.email,
                language=data.language.value,
                mode=data.mode.value,
                verified=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate OTP
        otp = _generate_otp()
        otp_hash = _hash_otp(otp)
        
        # Remove old OTPs
        db.query(DBOTP).filter(DBOTP.mobile == mobile).delete()
        
        # Store OTP
        otp_record = DBOTP(
            mobile=mobile,
            otp_hash=otp_hash,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            attempts=0
        )
        db.add(otp_record)
        db.commit()
        
        # Send OTP via SMS
        try:
            sms_gateway.send_sms(
                mobile=mobile,
                message=f"Your LegalSaathi OTP is: {otp}. Valid for 5 minutes."
            )
        except Exception as e:
            print(f"SMS sending failed: {e}")
            # In dev, return OTP anyway
        
        return {
            "success": True,
            "message": f"OTP sent to {mobile}",
            "dev_otp": otp if os.getenv("ENVIRONMENT") == "development" else None
        }
    
    finally:
        db.close()


def verify_otp_and_login(mobile: str, otp: str) -> Optional[LoginResult]:
    """Verify OTP and return tokens"""
    
    db = SessionLocal()
    
    try:
        # Find OTP record
        otp_record = db.query(DBOTP).filter(DBOTP.mobile == mobile).first()
        
        if not otp_record:
            raise ValueError("OTP not found. Please request a new one.")
        
        # Check expiry
        if datetime.utcnow() > otp_record.expires_at:
            db.delete(otp_record)
            db.commit()
            raise ValueError("OTP has expired. Please request a new one.")
        
        # Check attempts
        if otp_record.attempts >= 5:
            db.delete(otp_record)
            db.commit()
            raise ValueError("Too many OTP verification attempts. Please request a new OTP.")
        
        # Verify OTP
        otp_hash = _hash_otp(otp)
        if otp_record.otp_hash != otp_hash:
            otp_record.attempts += 1
            db.commit()
            raise ValueError("Invalid OTP. Please try again.")
        
        # Get or create user
        user = db.query(DBUser).filter_by(mobile=mobile).first()
        if not user:
            raise ValueError("User not found. Please register first.")
        
        # Mark user as verified
        user.verified = True
        user.verified_at = datetime.utcnow()
        
        # Delete OTP
        db.delete(otp_record)
        db.commit()
        
        # Create tokens
        tokens = JWTManager.create_tokens(str(user.user_id or user.id), mobile)
        
        return LoginResult(
            user=User(
                id=user.user_id or str(user.id),
                mobile=user.mobile,
                name=user.name,
                email=user.email,
                language=Language(user.language),
                mode=InterfaceMode(user.mode),
                created_at=user.created_at
            ),
            access_token=tokens['access_token']
        )
    
    finally:
        db.close()


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """Generate new access token from refresh token"""
    
    try:
        payload = JWTManager.verify_token(refresh_token, expected_type="refresh")
        
        # Create new access token
        tokens = JWTManager.create_tokens(
            payload['sub'],
            payload['mobile']
        )
        
        return {
            "access_token": tokens['access_token'],
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes in seconds
        }
    
    except HTTPException:
        raise


def logout(token: str) -> bool:
    """Logout by revoking token"""
    return JWTManager.revoke_token(token)
```

### Step 2.4: Update Main FastAPI App

Update: `main.py` - Add these endpoints:

```python
# Add at top
from backend.jwt_manager import get_current_user

# Add these endpoints

@app.post("/auth/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Get new access token using refresh token"""
    try:
        from backend.services.auth_service import refresh_access_token
        tokens = refresh_access_token(request.refresh_token)
        return tokens
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    try:
        # Log the logout event
        logger.info(f"User {current_user['mobile']} logged out")
        
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to logout")


# Update existing endpoints to use new dependency
@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    try:
        db = SessionLocal()
        user = db.query(DBUser).filter_by(mobile=current_user['mobile']).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.user_id or str(user.id),
            "mobile": user.mobile,
            "name": user.name,
            "email": user.email,
            "language": user.language,
            "mode": user.mode,
            "created_at": user.created_at.isoformat()
        }
    finally:
        db.close()
```

---

## PART 3: REDIS CACHING & RATE LIMITING (2 Days)

### Step 3.1: Install Redis

```bash
# macOS
brew install redis
redis-server

# Windows (using WSL)
wsl -d Ubuntu -u root apt-get install redis-server
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 3.2: Add to requirements.txt

```txt
redis>=5.0.0
slowapi>=0.1.8
```

### Step 3.3: Create Cache Manager

Create file: `backend/cache_manager.py`

```python
"""
Redis Cache Manager
"""
import redis
import json
import os
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    """Centralized cache management using Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            print("✅ Redis connection successful")
        except redis.ConnectionError:
            print("⚠️ Redis connection failed - caching disabled")
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        try:
            json_value = json.dumps(value)
            self.redis_client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def cache_user(self, user_id: str, user_data: dict, ttl: int = 86400):
        """Cache user for 24 hours"""
        self.set(f"user:{user_id}", user_data, ttl)
    
    def get_cached_user(self, user_id: str) -> Optional[dict]:
        """Get cached user"""
        return self.get(f"user:{user_id}")
    
    def cache_document(self, doc_id: str, doc_data: dict, ttl: int = 604800):
        """Cache document for 7 days"""
        self.set(f"doc:{doc_id}", doc_data, ttl)
    
    def get_cached_document(self, doc_id: str) -> Optional[dict]:
        """Get cached document"""
        return self.get(f"doc:{doc_id}")
    
    def increment_rate_limit(self, key: str, limit: int, window: int = 60) -> int:
        """Increment rate limit counter"""
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                self.redis_client.expire(key, window)
            return count
        except:
            return 0
    
    def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count"""
        try:
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except:
            return 0

# Global cache instance
cache_manager = CacheManager()
```

### Step 3.4: Add Rate Limiting

Create file: `backend/rate_limiter.py`

```python
"""
Rate Limiting using slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiter(app: FastAPI):
    """Setup rate limiting on FastAPI app"""
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later.",
                "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else 60
            }
        )
    
    app.state.limiter = limiter
    return app
```

### Step 3.5: Update main.py

```python
# Add to imports
from backend.cache_manager import cache_manager
from backend.rate_limiter import limiter, setup_rate_limiter

# Add after FastAPI initialization
app = FastAPI(...)
app = setup_rate_limiter(app)

# Add rate limiting to endpoints
@app.post("/auth/register")
@limiter.limit("5/minute")  # 5 attempts per minute
async def register(request: Request, data: UserRegister):
    # ... implementation

@app.post("/auth/verify-otp")
@limiter.limit("10/minute")  # 10 attempts per minute
async def verify_otp(request: Request, data: OTPRequest):
    # ... implementation

@app.post("/documents/draft")
@limiter.limit("10/minute")  # 10 documents per minute
async def draft_document(request: Request, data: DocumentDraftRequest, current_user: dict = Depends(get_current_user)):
    # ... implementation
```

---

## PART 4: TEST MIGRATION

### Step 4.1: Test Database Connection

Create file: `test_migration.py`

```python
"""
Test database migration
"""
import sys
sys.path.insert(0, '/path/to/project')

from backend.database.connection import get_db, engine
from backend.database.models import Base, User, Document

# Test 1: Create tables
print("Testing database connection...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully")

# Test 2: Insert test user
print("\nTesting user creation...")
db = next(get_db())
test_user = User(
    user_id="test_user_001",
    mobile="9876543210",
    name="Test User",
    email="test@example.com",
    language="en",
    mode="simple"
)
db.add(test_user)
db.commit()
print("✅ User created successfully")

# Test 3: Query user
print("\nTesting user query...")
user = db.query(User).filter_by(mobile="9876543210").first()
print(f"✅ User found: {user.name} ({user.mobile})")

# Test 4: Insert test document
print("\nTesting document creation...")
test_doc = Document(
    id="doc_test_001",
    user_id=test_user.id,
    title="Test Agreement",
    doc_type="rental_agreement",
    content="This is a test document",
    overall_risk="LOW"
)
db.add(test_doc)
db.commit()
print("✅ Document created successfully")

# Test 5: Query with relationship
print("\nTesting relationships...")
user_with_docs = db.query(User).filter_by(mobile="9876543210").first()
print(f"✅ User has {len(user_with_docs.documents)} documents")

db.close()
print("\n✅ All tests passed!")
```

### Step 4.2: Run Test

```bash
cd /path/to/project
python test_migration.py
```

---

## PART 5: DEPLOYMENT CHECKLIST

### Before Going Live

```
Security:
- [ ] Remove dev_otp from registration response
- [ ] Set SECRET_KEY to strong random value
- [ ] Enable HTTPS/SSL certificates
- [ ] Set ENVIRONMENT to "production"
- [ ] Disable DEBUG mode
- [ ] Add input validation on all endpoints
- [ ] Enable CORS properly (not allow *)
- [ ] Set secure cookie flags
- [ ] Enable rate limiting

Database:
- [ ] PostgreSQL running on production server
- [ ] Database backups enabled
- [ ] Connection pooling configured
- [ ] Indexes created on frequently queried columns
- [ ] Automated backups tested

Performance:
- [ ] Redis configured and running
- [ ] Caching TTLs set appropriately
- [ ] Gunicorn workers configured (4 x CPU cores)
- [ ] Nginx reverse proxy configured
- [ ] Load testing done (simulate 1000+ users)

Monitoring:
- [ ] Logging configured
- [ ] Error tracking setup (Sentry)
- [ ] Metrics collection setup (Prometheus)
- [ ] Health check endpoints tested
- [ ] Alerts configured

Testing:
- [ ] All API endpoints tested
- [ ] Database migration tested
- [ ] Authentication flow tested
- [ ] Error handling tested
- [ ] Rate limiting tested
```

---

## QUICK START (SUMMARY)

### Day 1: Database Setup
```bash
# 1. Install PostgreSQL
# 2. Create .env file
# 3. Run migration script
python scripts/migrate_data.py
```

### Day 2: Authentication
```bash
# 1. Update auth_service.py
# 2. Update main.py with new endpoints
# 3. Test authentication flow
python -m pytest tests/test_auth.py
```

### Day 3: Caching & Rate Limiting
```bash
# 1. Install Redis
redis-server
# 2. Update main.py with caching/rate limiting
# 3. Test load
python -m locust -f locustfile.py
```

---

## ESTIMATED TIMELINE

- **Database**: 1 day
- **Authentication**: 1 day
- **Caching & Rate Limiting**: 1 day
- **Testing & Deployment**: 2-3 days
- **Total**: 5-6 days

**You should be MVP-ready by end of Week 1** with this implementation plan.

---

## NEXT STEPS AFTER THESE FIXES

1. **Build React Frontend** (Week 2-3)
2. **Integrate Real LLM** (Week 3)
3. **Add Payments** (Week 3)
4. **Deploy to AWS** (Week 4)
5. **Launch MVP** (Week 4)

Good luck! 🚀
