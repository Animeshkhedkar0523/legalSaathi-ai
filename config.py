"""
Configuration Management for LegalSaathi
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///legal_saathi.db")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # SMS Gateway
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # SMS Alternative
    SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
    SMS_GATEWAY_API_KEY = os.getenv("SMS_GATEWAY_API_KEY", "")
    
    # Application
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Session
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
    TOKEN_EXPIRY_DAYS = int(os.getenv("TOKEN_EXPIRY_DAYS", 30))
    OTP_LENGTH = int(os.getenv("OTP_LENGTH", 6))
    OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 300))
    
    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@legalsaathi.com")
    
    # External Services
    INDIAN_KANOON_API_URL = os.getenv("INDIAN_KANOON_API_URL", "https://www.indkanoon.org/")
    LEGAL_DATABASE_URL = os.getenv("LEGAL_DATABASE_URL", "")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/legal_saathi.log")


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENVIRONMENT = "development"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENVIRONMENT = "production"


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    ENVIRONMENT = "testing"
    DATABASE_URL = "sqlite:///:memory:"


# Select config based on environment
config_name = os.getenv("ENVIRONMENT", "development")
if config_name == "production":
    config = ProductionConfig()
elif config_name == "testing":
    config = TestingConfig()
else:
    config = DevelopmentConfig()
