"""
Test Suite - Sample requests and integration tests
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestSuite:
    """API Test Suite"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.mobile = "9876543210"
        self.user_data = {
            "mobile": self.mobile,
            "name": "Test User",
            "email": "test@example.com",
            "language": "en",
            "mode": "simple"
        }
    
    def print_test(self, name: str):
        """Print test header"""
        print(f"\n{'='*60}")
        print(f"  TEST: {name}")
        print(f"{'='*60}")
    
    def print_response(self, response: requests.Response, name: str = ""):
        """Pretty print response"""
        try:
            data = response.json()
            print(f"✓ {name} [{response.status_code}]")
            print(json.dumps(data, indent=2)[:500])  # First 500 chars
        except:
            print(f"✗ {name} [{response.status_code}]")
            print(response.text[:200])
    
    def test_health_check(self):
        """Test: Health Check"""
        self.print_test("Health Check")
        response = requests.get(f"{self.base_url}/health")
        self.print_response(response, "Health Check")
        assert response.status_code == 200, "Health check failed"
        print("✅ PASSED")
    
    def test_registration(self):
        """Test: User Registration"""
        self.print_test("User Registration")
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=self.user_data
        )
        self.print_response(response, "Registration")
        assert response.status_code == 200, "Registration failed"
        
        data = response.json()
        if "dev_otp" in data:
            self.otp = data["dev_otp"]
            print(f"Dev OTP for testing: {self.otp}")
        print("✅ PASSED")
    
    def test_otp_verification(self):
        """Test: OTP Verification & Login"""
        self.print_test("OTP Verification & Login")
        
        if not hasattr(self, 'otp'):
            print("⚠️  Need to run registration first")
            self.test_registration()
        
        response = requests.post(
            f"{self.base_url}/auth/verify-otp",
            json={"mobile": self.mobile, "otp": self.otp}
        )
        self.print_response(response, "OTP Verification")
        assert response.status_code == 200, "OTP verification failed"
        
        data = response.json()
        self.token = data["access_token"]
        print(f"Token: {self.token[:50]}...")
        print("✅ PASSED")
    
    def test_get_user(self):
        """Test: Get Current User"""
        self.print_test("Get Current User")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=headers
        )
        self.print_response(response, "Get User")
        assert response.status_code == 200, "Get user failed"
        print("✅ PASSED")
    
    def test_draft_document(self):
        """Test: Draft Legal Document"""
        self.print_test("Draft Legal Document (Rental Agreement)")
        
        document_data = {
            "doc_type": "rental_agreement",
            "language": "en",
            "include_citations": True,
            "data": {
                "party_a": {
                    "name": "Rajesh Kumar",
                    "address": "123 MG Road, Bangalore",
                    "contact": "9876543210"
                },
                "party_b": {
                    "name": "Priya Singh",
                    "address": "456 Indiranagar, Bangalore",
                    "contact": "9876543211"
                },
                "property_address": "789 Koramangala, Bangalore",
                "monthly_rent": 35000,
                "security_deposit": 105000,
                "duration_months": 12,
                "start_date": "2026-05-01"
            }
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/draft",
            json=document_data,
            headers=headers
        )
        self.print_response(response, "Draft Document")
        assert response.status_code == 200, "Draft document failed"
        
        data = response.json()
        self.doc_id = data.get("document_id")
        print(f"Document ID: {self.doc_id}")
        print("✅ PASSED")
    
    def test_list_documents(self):
        """Test: List User Documents"""
        self.print_test("List User Documents")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/documents",
            headers=headers
        )
        self.print_response(response, "List Documents")
        assert response.status_code == 200, "List documents failed"
        print("✅ PASSED")
    
    def test_get_document(self):
        """Test: Get Specific Document"""
        self.print_test("Get Specific Document")
        
        if not hasattr(self, 'doc_id'):
            print("⚠️  Need to create a document first")
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/documents/{self.doc_id}",
            headers=headers
        )
        self.print_response(response, "Get Document")
        assert response.status_code == 200, "Get document failed"
        print("✅ PASSED")
    
    def test_risk_analysis(self):
        """Test: Risk Analysis"""
        self.print_test("Risk Analysis")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/{self.doc_id}/risk-analysis",
            headers=headers
        )
        self.print_response(response, "Risk Analysis")
        assert response.status_code == 200, "Risk analysis failed"
        print("✅ PASSED")
    
    def test_summarize(self):
        """Test: Document Summarization"""
        self.print_test("Document Summarization")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/{self.doc_id}/summarize?language=en",
            headers=headers
        )
        self.print_response(response, "Summarization")
        assert response.status_code == 200, "Summarization failed"
        print("✅ PASSED")
    
    def test_citations(self):
        """Test: Extract Citations"""
        self.print_test("Extract & Verify Citations")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/{self.doc_id}/citations",
            headers=headers
        )
        self.print_response(response, "Citations")
        assert response.status_code == 200, "Citations failed"
        print("✅ PASSED")
    
    def test_qa(self):
        """Test: Q&A"""
        self.print_test("Q&A on Document")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        qa_data = {
            "question": "What are the tenant's payment obligations?",
            "language": "en"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/{self.doc_id}/qa",
            json=qa_data,
            headers=headers
        )
        self.print_response(response, "Q&A")
        assert response.status_code == 200, "Q&A failed"
        print("✅ PASSED")
    
    def test_translation(self):
        """Test: Document Translation"""
        self.print_test("Document Translation")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/documents/{self.doc_id}/translate?target_language=hi",
            headers=headers
        )
        self.print_response(response, "Translation")
        assert response.status_code == 200, "Translation failed"
        print("✅ PASSED")
    
    def test_delete_document(self):
        """Test: Delete Document"""
        self.print_test("Delete Document")
        
        if not hasattr(self, 'doc_id'):
            self.test_draft_document()
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.delete(
            f"{self.base_url}/documents/{self.doc_id}",
            headers=headers
        )
        self.print_response(response, "Delete Document")
        assert response.status_code == 200, "Delete document failed"
        print("✅ PASSED")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("  LEGALSAATHI API TEST SUITE")
        print("="*60)
        
        try:
            self.test_health_check()
            self.test_registration()
            self.test_otp_verification()
            self.test_get_user()
            self.test_draft_document()
            self.test_list_documents()
            self.test_get_document()
            self.test_risk_analysis()
            self.test_summarize()
            self.test_citations()
            self.test_qa()
            self.test_translation()
            self.test_delete_document()
            
            print("\n" + "="*60)
            print("  ✅ ALL TESTS PASSED")
            print("="*60 + "\n")
        
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LegalSaathi API Test Suite")
    parser.add_argument("--base-url", default=BASE_URL, help="API base URL")
    parser.add_argument("--test", default="all", help="Specific test to run")
    
    args = parser.parse_args()
    
    suite = TestSuite(args.base_url)
    
    if args.test == "all":
        suite.run_all_tests()
    else:
        method_name = f"test_{args.test}"
        if hasattr(suite, method_name):
            getattr(suite, method_name)()
        else:
            print(f"Test '{args.test}' not found")
