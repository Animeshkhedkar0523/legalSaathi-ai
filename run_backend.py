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
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'python-dotenv',
        'pytesseract',
        'PyPDF2',
        'python-docx',
        'pillow'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
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
        "--host", "0.0.0.0",
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
