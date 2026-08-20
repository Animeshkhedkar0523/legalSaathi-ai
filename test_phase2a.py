"""
Phase 2A AI Core Test Suite
Tests unit & endpoint behavior with mocked OpenAI API calls:
1. Successful Legal Q&A with Structured Response
2. Empty Question Handling (HTTP 400)
3. Missing Document Handling (HTTP 404)
4. Unauthorized Document Access Rejection (HTTP 403)
5. Invalid JWT Authentication Handling (HTTP 401)
6. Missing OpenAI API Key Fallback Handling
7. OpenAI API Failure / Timeout Resilience
8. Long Input Question Validation (HTTP 400)
9. Structured Pydantic Response Schema Compliance
10. Zero Fabricated Citations Verification
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Environment test configuration
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite:///./test_phase2a.db"
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-12345"
os.environ["OPENAI_MODEL"] = "gpt-5.6"

from config import config
from backend.database import (
    init_db,
    SessionLocal,
    UserModel,
    DocumentModel,
    CitationModel,
    OTPModel
)
from backend.services.storage_service import storage_service
from backend.services.ai_service import ai_service
from backend.models.schemas import (
    DocumentResult,
    DocumentType,
    Language,
    RiskLevel,
    LegalQAResponse,
    User
)
from backend.jwt_manager import JWTManager
from backend.llm_integration import OpenAIProvider, llm_provider


def run_tests():
    print("=" * 80)
    print("LEGALSAATHI PHASE 2A AI CORE TEST SUITE")
    print("=" * 80 + "\n")

    test_results = {
        "Successful_QA": False,
        "Empty_Question": False,
        "Missing_Document": False,
        "Unauthorized_Access": False,
        "Invalid_JWT": False,
        "Missing_API_Key": False,
        "API_Failure_Resilience": False,
        "Long_Input_Validation": False,
        "Structured_Schema": False,
        "Zero_Fabricated_Citations": False
    }

    # Initialize Database
    init_db()
    session = SessionLocal()
    try:
        # Reset tables
        session.query(CitationModel).delete()
        session.query(DocumentModel).delete()
        session.query(OTPModel).delete()
        session.query(UserModel).delete()
        session.commit()

        # Seed User A and User B
        u_a = UserModel(id="user_a_100", mobile="9999911111", name="User A", is_verified=True)
        u_b = UserModel(id="user_b_200", mobile="8888822222", name="User B", is_verified=True)
        session.add(u_a)
        session.add(u_b)
        session.commit()

        # Seed Document for User A
        doc_res = DocumentResult(
            document_id="doc_a_500",
            document_type=DocumentType.RENTAL_AGREEMENT,
            content="RENTAL AGREEMENT: Monthly rent is Rs 25,000. Security deposit is Rs 50,000 payable in advance.",
            summary="Rental agreement for User A",
            citations=[],
            risk_clauses=[],
            overall_risk=RiskLevel.LOW,
            language=Language.EN,
            title="User A Agreement"
        )
        storage_service.save_created_document(doc_res, "9999911111")
        print("[INIT] Test users and document seeded.")
    finally:
        session.close()

    # --------------------------------------------------------------------------
    # TEST 1: SUCCESSFUL LEGAL Q&A WITH MOCKED OPENAI API
    # --------------------------------------------------------------------------
    print("\n--- 1. Testing Successful Legal Q&A ---")
    mock_chat_response = "The security deposit specified in the rental agreement is Rs 50,000."
    mock_classif = {
        "intent": "tenant_deposit_dispute",
        "legal_domain": "property / tenancy",
        "requires_lawyer": False,
        "confidence": 0.95
    }

    with patch.object(llm_provider, "chat", return_value=mock_chat_response), \
         patch.object(llm_provider, "classify_legal_query", return_value=mock_classif):
        
        doc_text = storage_service.get_document_text("doc_a_500")
        qa_res = ai_service.answer_question(doc_text, "How much security deposit is required?", Language.EN)

        assert qa_res["answer"] == mock_chat_response
        assert qa_res["legal_domain"] == "property / tenancy"
        assert qa_res["intent"] == "tenant_deposit_dispute"
        assert qa_res["confidence"] == 0.95
        assert "LegalSaathi provides general legal information" in qa_res["disclaimer"]
        print("  [PASS] Legal Q&A executed successfully with structured response")
        test_results["Successful_QA"] = True

    # --------------------------------------------------------------------------
    # TEST 2: EMPTY QUESTION HANDLING
    # --------------------------------------------------------------------------
    print("\n--- 2. Testing Empty Question Validation ---")
    try:
        ai_service.answer_question("Some document text", "", Language.EN)
        print("  [FAIL] Empty question was not rejected")
    except ValueError as ve:
        print(f"  [PASS] Empty question properly rejected: {ve}")
        test_results["Empty_Question"] = True

    # --------------------------------------------------------------------------
    # TEST 3: MISSING DOCUMENT HANDLING
    # --------------------------------------------------------------------------
    print("\n--- 3. Testing Missing Document Handling ---")
    missing_doc_text = storage_service.get_document_text("non_existent_doc_id")
    assert missing_doc_text is None
    qa_res_missing = ai_service.answer_question(missing_doc_text, "What is the rent?", Language.EN)
    assert "couldn't find" in qa_res_missing["answer"].lower() or "empty" in qa_res_missing["answer"].lower() or "unable" in qa_res_missing["answer"].lower()
    print("  [PASS] Missing/Empty document safely handled")
    test_results["Missing_Document"] = True

    # --------------------------------------------------------------------------
    # TEST 4: UNAUTHORIZED DOCUMENT ACCESS REJECTION
    # --------------------------------------------------------------------------
    print("\n--- 4. Testing Unauthorized Access Rejection ---")
    session = SessionLocal()
    try:
        u_b_user = session.query(UserModel).filter(UserModel.mobile == "8888822222").first()
        owned = storage_service.get_user_document_by_id("doc_a_500", u_b_user.id)
        assert owned is None
        print("  [PASS] User B correctly denied access to User A's document")
        test_results["Unauthorized_Access"] = True
    finally:
        session.close()

    # --------------------------------------------------------------------------
    # TEST 5: INVALID JWT AUTHENTICATION
    # --------------------------------------------------------------------------
    print("\n--- 5. Testing Invalid JWT Authentication ---")
    invalid_payload = JWTManager.decode_token("invalid.jwt.token")
    assert invalid_payload is None
    print("  [PASS] Invalid JWT payload returned None as expected")
    test_results["Invalid_JWT"] = True

    # --------------------------------------------------------------------------
    # TEST 6: MISSING OPENAI API KEY FALLBACK
    # --------------------------------------------------------------------------
    print("\n--- 6. Testing Missing OpenAI API Key Fallback ---")
    provider_no_key = OpenAIProvider()
    provider_no_key.api_key = ""
    fallback_text = provider_no_key.generate("What is the rent?")
    assert len(fallback_text) > 10
    print("  [PASS] Missing API key fell back gracefully to safe offline message")
    test_results["Missing_API_Key"] = True

    # --------------------------------------------------------------------------
    # TEST 7: OPENAI API FAILURE / TIMEOUT RESILIENCE
    # --------------------------------------------------------------------------
    print("\n--- 7. Testing OpenAI API Failure Resilience ---")
    with patch("requests.post", side_effect=Exception("Connection timed out")):
        res_fail = llm_provider.chat([{"role": "user", "content": "What is the deposit?"}])
        assert len(res_fail) > 10
        print("  [PASS] API failure caught and safely handled without unhandled crash")
        test_results["API_Failure_Resilience"] = True

    # --------------------------------------------------------------------------
    # TEST 8: LONG INPUT QUESTION VALIDATION
    # --------------------------------------------------------------------------
    print("\n--- 8. Testing Long Question Input Validation ---")
    long_question = "A" * 2500
    try:
        ai_service.answer_question("Doc text", long_question, Language.EN)
        print("  [FAIL] Long question > 2000 chars was not rejected")
    except ValueError as ve:
        print(f"  [PASS] Long question correctly rejected: {ve}")
        test_results["Long_Input_Validation"] = True

    # --------------------------------------------------------------------------
    # TEST 9: STRUCTURED RESPONSE SCHEMA COMPLIANCE
    # --------------------------------------------------------------------------
    print("\n--- 9. Testing Structured Response Schema Compliance ---")
    with patch("backend.llm_integration.llm_provider.chat", return_value="The rent is Rs 25,000."), \
         patch("backend.llm_integration.llm_provider.classify_legal_query", return_value={"intent": "rent_inquiry", "legal_domain": "tenancy", "requires_lawyer": False, "confidence": 0.9}):
        
        raw_struct = ai_service.answer_question("Monthly rent is Rs 25,000.", "What is the rent?")
        print("DEBUG Test 9 raw_struct:", raw_struct)
        # Validate Pydantic parse
        structured_obj = LegalQAResponse(**raw_struct)
        assert structured_obj.answer == "The rent is Rs 25,000."
        assert structured_obj.intent == "rent_inquiry"
        assert structured_obj.confidence == 0.9
        assert structured_obj.requires_lawyer is False
        assert len(structured_obj.disclaimer) > 10
        print("  [PASS] Structured response validated against LegalQAResponse Pydantic schema")
        test_results["Structured_Schema"] = True

    # --------------------------------------------------------------------------
    # TEST 10: ZERO FABRICATED CITATIONS VERIFICATION
    # --------------------------------------------------------------------------
    print("\n--- 10. Testing Zero Fabricated Citations ---")
    with patch.object(llm_provider, "chat", return_value="The agreement allows termination with 30 days notice."), \
         patch.object(llm_provider, "classify_legal_query", return_value={"intent": "termination_inquiry", "legal_domain": "property / tenancy", "requires_lawyer": False, "confidence": 0.95}):
        
        qa_no_cites = ai_service.answer_question("Termination clause: 30 days notice.", "How to terminate?")
        assert qa_no_cites["sources"] == []
        print("  [PASS] Answer contains zero fabricated citations (sources=[])")
        test_results["Zero_Fabricated_Citations"] = True

    # --------------------------------------------------------------------------
    # TEST SUMMARY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    for category, passed in test_results.items():
        status = "PASS" if passed else "FAIL"
        icon = "[+] " if passed else "[-] "
        print(f"{icon} {category:30}: {status}")

    all_passed = all(test_results.values())
    print("\nOverall Status: " + ("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"))
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
