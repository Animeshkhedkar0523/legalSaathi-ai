"""
Authentication Service - Database-backed User Registration, OTP Management, and JWT Authentication
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from backend.database import SessionLocal, UserModel, OTPModel
from backend.models.schemas import User, UserRegister, LoginResult, Language, InterfaceMode
from backend.jwt_manager import JWTManager
from backend.sms_gateway import sms_gateway
from config import config


def _generate_otp() -> str:
    """Generate a random numeric OTP string"""
    length = getattr(config, "OTP_LENGTH", 6)
    return ''.join(random.choices(string.digits, k=length))


def register_and_send_otp(data: UserRegister) -> dict:
    """
    Register a user or update user profile and send OTP via SMS gateway.
    Handles rate-limiting resend cooldowns and environment-specific response formatting.
    """
    mobile = data.mobile.strip()
    if not mobile or len(mobile) < 10 or not mobile.isdigit():
        raise ValueError("Invalid phone number format. Must be a 10-digit mobile number.")
    
    session = SessionLocal()
    try:
        # Check resend cooldown
        existing_otp = (
            session.query(OTPModel)
            .filter(OTPModel.mobile == mobile)
            .order_by(OTPModel.created_at.desc())
            .first()
        )
        
        cooldown_sec = getattr(config, "OTP_RESEND_COOLDOWN_SECONDS", 60)
        if existing_otp and existing_otp.last_sent_at:
            elapsed = (datetime.utcnow() - existing_otp.last_sent_at).total_seconds()
            if elapsed < cooldown_sec:
                remaining = int(cooldown_sec - elapsed)
                raise ValueError(f"Please wait {remaining} seconds before requesting another OTP.")

        # Query or create user in DB
        user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
        lang_val = data.language.value if hasattr(data.language, 'value') else str(data.language)
        mode_val = data.mode.value if hasattr(data.mode, 'value') else str(data.mode)
        
        if user:
            user.name = data.name
            user.email = data.email or user.email
            user.language = lang_val
            user.interface_mode = mode_val
            user.updated_at = datetime.utcnow()
        else:
            user = UserModel(
                mobile=mobile,
                name=data.name,
                email=data.email,
                language=lang_val,
                interface_mode=mode_val,
                is_verified=False
            )
            session.add(user)
        
        session.flush()

        # Generate OTP
        otp_code = _generate_otp()
        expiry_sec = getattr(config, "OTP_EXPIRY_SECONDS", 300)
        expires_at = datetime.utcnow() + timedelta(seconds=expiry_sec)

        if existing_otp:
            existing_otp.otp_code = otp_code
            existing_otp.expires_at = expires_at
            existing_otp.attempts = 0
            existing_otp.last_sent_at = datetime.utcnow()
        else:
            otp_record = OTPModel(
                mobile=mobile,
                otp_code=otp_code,
                expires_at=expires_at,
                attempts=0,
                last_sent_at=datetime.utcnow()
            )
            session.add(otp_record)
        
        session.commit()

        # Send OTP via SMS Gateway
        sms_success, provider = sms_gateway.send_otp(mobile, otp_code)
        
        response = {
            "success": True,
            "message": f"OTP sent to {mobile}"
        }

        # NEVER return dev_otp in production
        if getattr(config, "ENVIRONMENT", "development") != "production":
            response["dev_otp"] = otp_code
            
        return response
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def verify_otp_and_login(mobile: str, otp: str) -> Optional[LoginResult]:
    """
    Verify OTP code, mark user as verified, and issue signed JWT tokens.
    Enforces maximum attempt limits and expiration checks.
    """
    mobile = mobile.strip()
    session = SessionLocal()
    try:
        otp_record = (
            session.query(OTPModel)
            .filter(OTPModel.mobile == mobile)
            .order_by(OTPModel.created_at.desc())
            .first()
        )

        if not otp_record:
            raise ValueError("OTP not found. Please register or request an OTP first.")

        max_attempts = getattr(config, "OTP_MAX_ATTEMPTS", 5)
        if otp_record.attempts >= max_attempts:
            session.delete(otp_record)
            session.commit()
            raise ValueError("Too many failed attempts. Please request a new OTP.")

        if datetime.utcnow() > otp_record.expires_at:
            session.delete(otp_record)
            session.commit()
            raise ValueError("OTP has expired. Please request a new one.")

        if otp_record.otp_code != otp:
            otp_record.attempts += 1
            session.commit()
            remaining_attempts = max_attempts - otp_record.attempts
            if remaining_attempts <= 0:
                raise ValueError("Too many failed attempts. Please request a new OTP.")
            raise ValueError(f"Invalid OTP. {remaining_attempts} attempts remaining.")

        # OTP is valid -> load user
        user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
        if not user:
            raise ValueError("User profile not found. Please register first.")

        user.is_verified = True
        user.updated_at = datetime.utcnow()
        session.delete(otp_record)
        session.commit()

        # Build user Pydantic schema
        try:
            lang_enum = Language(user.language)
        except ValueError:
            lang_enum = Language.EN

        try:
            mode_enum = InterfaceMode(user.interface_mode)
        except ValueError:
            mode_enum = InterfaceMode.SIMPLE

        user_schema = User(
            id=user.id,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            language=lang_enum,
            mode=mode_enum,
            created_at=user.created_at
        )

        # Generate JWT access token
        tokens = JWTManager.create_tokens(user_id=user.id, mobile=user.mobile)
        access_token = tokens["access_token"]

        return LoginResult(
            user=user_schema,
            access_token=access_token
        )
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_user_by_mobile(mobile: str) -> Optional[User]:
    """Retrieve user profile by mobile number"""
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter(UserModel.mobile == mobile).first()
        if not user:
            return None
        
        try:
            lang_enum = Language(user.language)
        except ValueError:
            lang_enum = Language.EN

        try:
            mode_enum = InterfaceMode(user.interface_mode)
        except ValueError:
            mode_enum = InterfaceMode.SIMPLE

        return User(
            id=user.id,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            language=lang_enum,
            mode=mode_enum,
            created_at=user.created_at
        )
    finally:
        session.close()


def get_user_by_id(user_id: str) -> Optional[User]:
    """Retrieve user profile by user ID"""
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None

        try:
            lang_enum = Language(user.language)
        except ValueError:
            lang_enum = Language.EN

        try:
            mode_enum = InterfaceMode(user.interface_mode)
        except ValueError:
            mode_enum = InterfaceMode.SIMPLE

        return User(
            id=user.id,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            language=lang_enum,
            mode=mode_enum,
            created_at=user.created_at
        )
    finally:
        session.close()


def verify_token(token: str) -> Optional[str]:
    """Verify access token and return mobile number if valid"""
    try:
        payload = JWTManager.verify_token(token)
        if payload and payload.get("type") == "access":
            return payload.get("mobile")
        return None
    except Exception:
        return None


def logout(token: str) -> bool:
    """Revoke user session token"""
    return JWTManager.revoke_token(token)
