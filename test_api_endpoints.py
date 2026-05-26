"""
API Testing Script - Test all endpoints with sample requests
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, description: str = "") -> Dict[str, Any]:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=HEADERS, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=HEADERS, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=5)
        else:
            return {"success": False, "error": "Unknown method"}
        
        success = response.status_code < 400
        results["tests"].append({
            "description": description,
            "method": method,
            "endpoint": endpoint,
            "status_code": response.status_code,
            "success": success
        })
        
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        print(f"{'✅' if success else '❌'} {method:6} {endpoint:40} [{response.status_code}]")
        if not success and response.text:
            print(f"   Error: {response.text[:100]}")
        
        return {"success": success, "status": response.status_code, "data": response.json() if response.text else None}
    
    except Exception as e:
        results["failed"] += 1
        results["tests"].append({
            "description": description,
            "method": method,
            "endpoint": endpoint,
            "error": str(e),
            "success": False
        })
        print(f"❌ {method:6} {endpoint:40} [ERROR: {str(e)[:50]}]")
        return {"success": False, "error": str(e)}


def main():
    """Run all API tests"""
    print("\n" + "="*80)
    print("🧪 LEGALSAATHI API TESTING")
    print("="*80 + "\n")
    
    # Test 1: Health Check
    print("📋 HEALTH CHECK")
    print("-" * 80)
    test_endpoint("GET", "/", description="Root endpoint")
    print()
    
    # Test 2: Authentication Endpoints
    print("🔐 AUTHENTICATION ENDPOINTS")
    print("-" * 80)
    
    # Register endpoint
    register_data = {
        "mobile": "+919999999999",
        "full_name": "Test User",
        "email": "test@example.com"
    }
    register_response = test_endpoint("POST", "/auth/register", register_data, "Register user")
    
    # Verify OTP endpoint
    verify_data = {
        "mobile": "+919999999999",
        "otp": "000000"  # Development OTP
    }
    verify_response = test_endpoint("POST", "/auth/verify-otp", verify_data, "Verify OTP")
    
    # Extract token if available
    token = None
    if verify_response["success"] and verify_response["data"]:
        token = verify_response["data"].get("access_token")
    
    if token:
        # Get current user
        auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        print(f"✅ Token obtained: {token[:20]}...")
        test_endpoint("GET", "/auth/me", description="Get current user")
    
    print()
    
    # Test 3: Document Generation Endpoints
    print("📄 DOCUMENT GENERATION")
    print("-" * 80)
    
    draft_data = {
        "doc_type": "employment_agreement",
        "data": {
            "company_name": "Acme Corp",
            "employee_name": "John Doe",
            "position": "Senior Developer",
            "salary": 100000,
            "start_date": "2026-06-01"
        },
        "language": "en",
        "include_citations": False
    }
    test_endpoint("POST", "/documents/draft", draft_data, "Generate document draft")
    print()
    
    # Test 4: Document Analysis Endpoints
    print("🔍 DOCUMENT ANALYSIS")
    print("-" * 80)
    
    analyze_data = {
        "document_text": "This employment agreement is valid for one year. The employee agrees to work 40 hours per week."
    }
    
    test_endpoint("POST", "/documents/analyze/risk-analysis", analyze_data, "Risk analysis")
    test_endpoint("POST", "/documents/analyze/summarize", analyze_data, "Summarize document")
    test_endpoint("POST", "/documents/analyze/citations", analyze_data, "Extract citations")
    
    qa_data = {
        "document_text": "The employee salary is $100,000 per year.",
        "question": "What is the employee's salary?"
    }
    test_endpoint("POST", "/documents/analyze/qa", qa_data, "Question & Answer")
    
    translate_data = {
        "text": "This is an important legal document.",
        "target_language": "hi"
    }
    test_endpoint("POST", "/documents/analyze/translate", translate_data, "Translate document")
    print()
    
    # Test 5: Document Management
    print("📁 DOCUMENT MANAGEMENT")
    print("-" * 80)
    test_endpoint("GET", "/documents", description="List documents")
    test_endpoint("GET", "/documents/123", description="Get specific document")
    print()
    
    # Test 6: System Endpoints
    print("⚙️  SYSTEM ENDPOINTS")
    print("-" * 80)
    test_endpoint("GET", "/health", description="Health check")
    test_endpoint("GET", "/cache/stats", description="Cache statistics")
    test_endpoint("GET", "/ratelimit/stats", description="Rate limit statistics")
    print()
    
    # Summary
    print("="*80)
    print(f"📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed'] / (results['passed'] + results['failed']) * 100):.1f}%\n")
    
    return results


if __name__ == "__main__":
    try:
        results = main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at http://localhost:8000")
        print("Make sure the server is running: python run_backend.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
