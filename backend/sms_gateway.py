"""
SMS Gateway Integration - Twilio, Textlocal, and fallback
"""
import os
import requests
from typing import Tuple, Optional
from backend.logging_config import get_logger

logger = get_logger("sms_gateway")


class SMSProvider:
    """Abstract SMS provider"""
    
    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        raise NotImplementedError


class TwilioProvider(SMSProvider):
    """Twilio SMS provider - has free trial"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        """Send SMS via Twilio"""
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Twilio credentials not configured")
            return False, "Twilio not configured"
        
        try:
            data = {
                "From": self.phone_number,
                "To": phone,
                "Body": message
            }
            
            response = requests.post(
                self.api_url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"SMS sent to {phone}")
                return True, response.json()["sid"]
            else:
                logger.error(f"Twilio error: {response.text}")
                return False, response.text
        
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False, str(e)


class TextlocalProvider(SMSProvider):
    """Textlocal SMS provider - free credits available"""
    
    def __init__(self):
        self.api_key = os.getenv("TEXTLOCAL_API_KEY", "")
        self.api_url = "https://api.textlocal.in/send/"
    
    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        """Send SMS via Textlocal"""
        if not self.api_key:
            logger.warning("Textlocal API key not configured")
            return False, "Textlocal not configured"
        
        try:
            # Remove +91 prefix if present for Indian numbers
            phone = phone.replace("+91", "").replace("+", "")
            
            params = {
                "apikey": self.api_key,
                "numbers": phone,
                "message": message
            }
            
            response = requests.post(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    logger.info(f"SMS sent to {phone}")
                    return True, data.get("messageid", "")
                else:
                    logger.error(f"Textlocal error: {data}")
                    return False, data.get("errors", [{}])[0].get("message", "Unknown error")
            else:
                return False, response.text
        
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False, str(e)


class DummySMSProvider(SMSProvider):
    """Dummy SMS provider for development"""
    
    def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        """Log SMS instead of sending"""
        logger.info(f"[DUMMY SMS] To: {phone}, Message: {message}")
        return True, f"DUMMY_ID_{hash(phone)}"


class SMSGateway:
    """SMS Gateway wrapper with fallback"""
    
    def __init__(self):
        self.providers = []
        
        # Add Twilio if configured
        twilio = TwilioProvider()
        if twilio.account_sid and twilio.auth_token:
            self.providers.append(("twilio", twilio))
        
        # Add Textlocal if configured
        textlocal = TextlocalProvider()
        if textlocal.api_key:
            self.providers.append(("textlocal", textlocal))
        
        # Always add dummy provider
        self.providers.append(("dummy", DummySMSProvider()))
    
    def send_sms(self, phone: str, message: str) -> Tuple[bool, str, str]:
        """
        Send SMS with automatic fallback
        Returns: (success, message_id, provider_name)
        """
        for provider_name, provider in self.providers:
            try:
                success, msg_id = provider.send_sms(phone, message)
                if success:
                    return True, msg_id, provider_name
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                continue
        
        return False, "", "none"
    
    def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        """Send OTP SMS"""
        message = f"Your LegalSaathi OTP is: {otp}. Valid for 5 minutes."
        success, msg_id, provider = self.send_sms(phone, message)
        
        if success:
            logger.info(f"OTP sent via {provider} to {phone}")
        else:
            logger.error(f"Failed to send OTP to {phone}")
        
        return success, provider


# Global SMS gateway instance
sms_gateway = SMSGateway()
