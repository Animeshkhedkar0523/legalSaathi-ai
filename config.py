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
    
    # JWT Authentication
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"))
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # CORS
    CORS_ORIGINS = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000,http://127.0.0.1:8501").split(",") 
        if origin.strip()
    ]
    
    # OTP & Security
    OTP_LENGTH = int(os.getenv("OTP_LENGTH", 6))
    OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 300))
    OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", 60))
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio")
    
    # Session
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
    TOKEN_EXPIRY_DAYS = int(os.getenv("TOKEN_EXPIRY_DAYS", 30))
    
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


def validate_environment() -> None:
    """
    Validate startup environment variables.
    In production mode, fail fast if required secrets or configurations are missing.
    """
    if config.ENVIRONMENT == "production":
        missing_vars = []
        if not config.SECRET_KEY or config.SECRET_KEY == "dev-secret-key":
            missing_vars.append("SECRET_KEY")
        if not config.JWT_SECRET_KEY or "dev-secret-key" in config.JWT_SECRET_KEY:
            missing_vars.append("JWT_SECRET_KEY")
        if not config.DATABASE_URL or config.DATABASE_URL == "sqlite:///legal_saathi.db":
            missing_vars.append("DATABASE_URL (Production requires a production database URL)")
        
        if config.SMS_PROVIDER.lower() == "twilio":
            if not config.TWILIO_ACCOUNT_SID:
                missing_vars.append("TWILIO_ACCOUNT_SID")
            if not config.TWILIO_AUTH_TOKEN:
                missing_vars.append("TWILIO_AUTH_TOKEN")
            if not config.TWILIO_PHONE_NUMBER:
                missing_vars.append("TWILIO_PHONE_NUMBER")
                
        if missing_vars:
            raise ValueError(
                f"Production environment validation failed. Missing or insecure variables: {', '.join(missing_vars)}"
            )

