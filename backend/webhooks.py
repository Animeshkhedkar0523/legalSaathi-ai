"""
Webhook System - For notifying external services
"""
import uuid
import json
import requests
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
from backend.logging_config import get_logger

logger = get_logger("webhooks")


class WebhookEvent(str, Enum):
    """Webhook event types"""
    # Auth events
    USER_REGISTERED = "user.registered"
    USER_VERIFIED = "user.verified"
    USER_LOGGED_OUT = "user.logged_out"
    
    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_SCANNED = "document.scanned"
    DOCUMENT_ANALYZED = "document.analyzed"
    DOCUMENT_DELETED = "document.deleted"
    
    # Error events
    ERROR_OCCURRED = "error.occurred"


class Webhook:
    """Webhook model"""
    
    def __init__(
        self,
        url: str,
        event: WebhookEvent,
        secret: str = "",
        active: bool = True,
        user_id: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.url = url
        self.event = event
        self.secret = secret or str(uuid.uuid4())
        self.active = active
        self.user_id = user_id
        self.created_at = datetime.utcnow().isoformat()
        self.last_triggered = None
        self.failure_count = 0
        self.max_retries = 3
    
    def generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "event": self.event.value,
            "active": self.active,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "failure_count": self.failure_count
        }


class WebhookManager:
    """Manage webhooks and trigger events"""
    
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.event_handlers: Dict[WebhookEvent, List[Callable]] = {}
    
    def register_webhook(
        self,
        url: str,
        event: WebhookEvent,
        secret: str = "",
        user_id: Optional[str] = None
    ) -> Webhook:
        """Register a new webhook"""
        webhook = Webhook(url, event, secret, user_id=user_id)
        self.webhooks[webhook.id] = webhook
        logger.info(f"Webhook registered: {webhook.id} for {event.value}")
        return webhook
    
    def unregister_webhook(self, webhook_id: str, user_id: Optional[str] = None) -> bool:
        """Unregister a webhook"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return False
        if user_id and webhook.user_id != user_id:
            return False
        del self.webhooks[webhook_id]
        logger.info(f"Webhook unregistered: {webhook_id}")
        return True
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID"""
        return self.webhooks.get(webhook_id)
    
    def list_webhooks(self, event: Optional[WebhookEvent] = None, user_id: Optional[str] = None) -> List[Webhook]:
        """List all or filtered webhooks"""
        webhooks = list(self.webhooks.values())
        if event:
            webhooks = [w for w in webhooks if w.event == event]
        if user_id:
            webhooks = [w for w in webhooks if w.user_id == user_id]
        return webhooks
    
    def trigger_webhook(
        self,
        event: WebhookEvent,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Dict[str, Dict]:
        """Trigger webhooks for an event"""
        results = {}
        
        # Get matching webhooks
        matching_webhooks = [
            w for w in self.webhooks.values()
            if w.event == event and w.active
        ]
        
        if not matching_webhooks:
            logger.info(f"No webhooks registered for event: {event.value}")
            return results
        
        # Prepare payload
        payload = {
            "id": str(uuid.uuid4()),
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "user_id": user_id
        }
        
        payload_json = json.dumps(payload)
        
        # Trigger each webhook
        for webhook in matching_webhooks:
            results[webhook.id] = self._send_webhook(webhook, payload_json)
        
        return results
    
    def _send_webhook(self, webhook: Webhook, payload_json: str) -> Dict:
        """Send webhook request with retries"""
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": webhook.id,
            "X-Webhook-Signature": webhook.generate_signature(payload_json)
        }
        
        for attempt in range(webhook.max_retries):
            try:
                response = requests.post(
                    webhook.url,
                    data=payload_json,
                    headers=headers,
                    timeout=10
                )
                
                webhook.last_triggered = datetime.utcnow().isoformat()
                
                if response.status_code < 400:
                    webhook.failure_count = 0
                    logger.info(f"Webhook {webhook.id} succeeded")
                    return {
                        "status": "success",
                        "status_code": response.status_code,
                        "attempt": attempt + 1
                    }
                else:
                    webhook.failure_count += 1
                    logger.warning(f"Webhook {webhook.id} failed: {response.status_code}")
            
            except requests.Timeout:
                webhook.failure_count += 1
                logger.warning(f"Webhook {webhook.id} timeout (attempt {attempt + 1})")
            
            except Exception as e:
                webhook.failure_count += 1
                logger.error(f"Webhook {webhook.id} error: {e}")
            
            # Retry after short delay
            if attempt < webhook.max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # Disable webhook after max failures
        if webhook.failure_count >= webhook.max_retries:
            webhook.active = False
            logger.error(f"Webhook {webhook.id} disabled after {webhook.failure_count} failures")
        
        return {
            "status": "failed",
            "failure_count": webhook.failure_count,
            "disabled": not webhook.active
        }
    
    def register_event_handler(
        self,
        event: WebhookEvent,
        handler: Callable
    ) -> None:
        """Register a local event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
        logger.info(f"Event handler registered for {event.value}")
    
    def trigger_event(self, event: WebhookEvent, data: Dict) -> None:
        """Trigger local event handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")


# Global webhook manager
webhook_manager = WebhookManager()
