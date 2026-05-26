#!/usr/bin/env python
"""
LegalSaathi Backend Server Startup Script
"""
import os
import sys
import subprocess

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_dependencies():
    """Check if all required packages are installed"""
    # Map package names to their import names
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'python-dotenv': 'dotenv',
        'pytesseract': 'pytesseract',
        'PyPDF2': 'PyPDF2',
        'python-docx': 'docx',
        'pillow': 'PIL'
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("❌ Missing packages:", ", ".join(missing))
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies installed")


def main():
    """Start the FastAPI server"""
    check_dependencies()
    
    print("\n" + "="*60)
    print("🏛️  LegalSaathi Backend API")
    print("="*60)
    
    # Get environment
    environment = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"Environment: {environment}")
    print(f"Debug Mode: {debug}")
    print("\n📚 API Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - OpenAPI JSON: http://localhost:8000/openapi.json")
    print("\n⚠️  Press Ctrl+C to stop the server\n")
    
    # Start server
    reload = "--reload" if debug else ""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    
    if debug:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
