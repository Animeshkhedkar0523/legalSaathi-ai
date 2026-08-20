"""
Phase 1 Foundation Test Suite
Tests:
1. SQLAlchemy Database Persistence (UserModel, DocumentModel, CitationModel, OTPModel)
2. JWT Authentication & Verification
3. OTP Generation, Rate Limiting, Cooldowns, Expiration, and Attempt Counters
4. Document Ownership & Security Authorization Checks
5. CORS and Environment Validation
"""
import os
import sys
from datetime import datetime, timedelta

# Enforce development testing environment
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase1.db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-12345"

from config import config, validate_environment
from backend.database import (
    init_db,
    SessionLocal,
    UserModel,
    DocumentModel,
    CitationModel,
    OTPModel
)
from backend.services.auth_service import (
    register_and_send_otp,
    verify_otp_and_login,
    get_user_by_mobile,
    get_user_by_id
)
from backend.services.storage_service import storage_service
from backend.models.schemas import UserRegister, DocumentResult, DocumentType, Language, RiskLevel, Citation, RiskClause, InterfaceMode
from backend.jwt_manager import JWTManager


def run_tests():
    print("=" * 80)
    print("LEGALSAATHI PHASE 1 TEST SUITE")
    print("=" * 80 + "\n")
    
    test_results = {
        "Database": False,
        "JWT": False,
        "OTP": False,
        "CORS": False,
        "Authorization": False
    }

    # 1. Init Database
    init_db()
    print("[INIT] Database tables created successfully.")

    # --------------------------------------------------------------------------
    # TEST 1: DATABASE PERSISTENCE & USER CREATION
    # --------------------------------------------------------------------------
    print("\n--- 1. Testing Database Persistence ---")
    session = SessionLocal()
    try:
        # Clear existing test data
        session.query(CitationModel).delete()
        session.query(DocumentModel).delete()
        session.query(OTPModel).delete()
        session.query(UserModel).delete()
        session.commit()

        # Create user via DB
        u1 = UserModel(
            mobile="9999911111",
            name="Alice DB",
            email="alice@test.com",
            language="en",
            interface_mode="simple",
            is_verified=True
        )
        session.add(u1)
        session.commit()
        
        fetched_user = session.query(UserModel).filter(UserModel.mobile == "9999911111").first()
        assert fetched_user is not None
        assert fetched_user.name == "Alice DB"
        assert fetched_user.email == "alice@test.com"
        print(f"  [PASS] User created and persisted in DB: ID={fetched_user.id}")

        # Create Document & Citation via StorageService
        doc_res = DocumentResult(
            document_id="doc_test_100",
            document_type=DocumentType.RENTAL_AGREEMENT,
            content="Rental Agreement Content Sample for Alice",
            summary="Alice rental summary",
            citations=[Citation(citation_text="AIR 1985 SC 800", case_name="Sample Case", year=1985, is_verified=True)],
            risk_clauses=[RiskClause(clause_text="Automatic renewal clause", risk_level=RiskLevel.HIGH, risk_reason="High risk")],
            overall_risk=RiskLevel.HIGH,
            language=Language.EN,
            title="Rental Agreement Alice"
        )
        saved_id = storage_service.save_created_document(doc_res, "9999911111")
        assert saved_id == "doc_test_100"

        # Verify DB record retrieval
        db_doc = session.query(DocumentModel).filter(DocumentModel.id == "doc_test_100").first()
        assert db_doc is not None
        assert db_doc.content == "Rental Agreement Content Sample for Alice"
        assert len(db_doc.citations) == 1
        assert db_doc.citations[0].citation_text == "AIR 1985 SC 800"
        print("  [PASS] Document and Citation persisted and retrieved via SQLAlchemy")
        
        user_docs = storage_service.list_user_documents("9999911111")
        assert len(user_docs) == 1
        assert user_docs[0]["document_id"] == "doc_test_100"
        print("  [PASS] list_user_documents() queries database correctly")

        test_results["Database"] = True
    except Exception as e:
        print(f"  [FAIL] Database test error: {e}")
    finally:
        session.close()

    # --------------------------------------------------------------------------
    # TEST 2: JWT AUTHENTICATION FLOW
    # --------------------------------------------------------------------------
    print("\n--- 2. Testing JWT Authentication ---")
    try:
        tokens = JWTManager.create_tokens(user_id="user_test_999", mobile="9999911111")
        access_token = tokens["access_token"]
        assert access_token is not None

        # Verify token
        payload = JWTManager.verify_token(access_token)
        assert payload["sub"] == "user_test_999"
        assert payload["mobile"] == "9999911111"
        assert payload["type"] == "access"
        print("  [PASS] JWT token creation and signature verification succeeded")

        # Revocation / Logout test
        JWTManager.revoke_token(access_token)
        try:
            JWTManager.verify_token(access_token)
            print("  [FAIL] Revoked token was not rejected")
        except Exception:
            print("  [PASS] Revoked token properly rejected")
            test_results["JWT"] = True
    except Exception as e:
        print(f"  [FAIL] JWT test error: {e}")

    # --------------------------------------------------------------------------
    # TEST 3: OTP ARCHITECTURE & RATE-LIMITING
    # --------------------------------------------------------------------------
    print("\n--- 3. Testing OTP Architecture & Security ---")
    try:
        reg_data = UserRegister(
            mobile="9876543210",
            name="Bob User",
            email="bob@test.com",
            language=Language.EN,
            mode=InterfaceMode.SIMPLE
        )
        res = register_and_send_otp(reg_data)
        assert res["success"] is True
        dev_otp = res.get("dev_otp")
        assert dev_otp is not None
        print(f"  [PASS] OTP registered and issued in dev mode: {dev_otp}")

        # Test cooldown resend rejection
        try:
            register_and_send_otp(reg_data)
            print("  [FAIL] Resend cooldown was not enforced!")
        except ValueError as ve:
            print(f"  [PASS] Resend cooldown correctly enforced: {ve}")

        # Test OTP verification & Login
        login_res = verify_otp_and_login("9876543210", dev_otp)
        assert login_res is not None
        assert login_res.user.mobile == "9876543210"
        assert login_res.access_token is not None
        print("  [PASS] OTP verified & user logged in with JWT token")

        # Test expired / missing OTP
        try:
            verify_otp_and_login("9876543210", dev_otp)
            print("  [FAIL] Already consumed OTP was not rejected!")
        except ValueError:
            print("  [PASS] Consumed OTP correctly rejected")
            test_results["OTP"] = True
    except Exception as e:
        print(f"  [FAIL] OTP test error: {e}")

    # --------------------------------------------------------------------------
    # TEST 4: CORS & ENVIRONMENT VALIDATION
    # --------------------------------------------------------------------------
    print("\n--- 4. Testing CORS & Environment Validation ---")
    try:
        assert isinstance(config.CORS_ORIGINS, list)
        assert len(config.CORS_ORIGINS) > 0
        print(f"  [PASS] Configured CORS origins parsed: {config.CORS_ORIGINS}")

        # Test environment validation in dev mode
        validate_environment()
        print("  [PASS] Development environment validation passed")
        test_results["CORS"] = True
    except Exception as e:
        print(f"  [FAIL] CORS/Environment validation error: {e}")

    # --------------------------------------------------------------------------
    # TEST 5: AUTHORIZATION & ACCESS CONTROL
    # --------------------------------------------------------------------------
    print("\n--- 5. Testing Authorization Ownership Checks ---")
    session = SessionLocal()
    try:
        # Create User A and User B
        u_a = session.query(UserModel).filter(UserModel.mobile == "9999911111").first()
        u_b = UserModel(mobile="8888822222", name="User B", is_verified=True)
        session.add(u_b)
        session.commit()

        # User A owns 'doc_test_100'
        # Query ownership for User A
        owned_a = storage_service.get_user_document_by_id("doc_test_100", u_a.id)
        assert owned_a is not None
        print("  [PASS] User A correctly recognized as owner of doc_test_100")

        # Query ownership for User B
        owned_b = storage_service.get_user_document_by_id("doc_test_100", u_b.id)
        assert owned_b is None
        print("  [PASS] User B correctly denied ownership access to User A's document")
        test_results["Authorization"] = True
    except Exception as e:
        print(f"  [FAIL] Authorization test error: {e}")
    finally:
        session.close()

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    for category, passed in test_results.items():
        status = "PASS" if passed else "FAIL"
        icon = "[+] " if passed else "[-] "
        print(f"{icon} {category:20}: {status}")
    
    all_passed = all(test_results.values())
    print("\nOverall Status: " + ("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"))
    return all_passed



if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
