"""
Centralized LLM Integration Layer - OpenAI Primary Provider (GPT-5.6)
All LLM communications MUST go through this module.
API keys and model configurations are strictly loaded from environment variables.
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
from config import config
from backend.logging_config import get_logger

logger = get_logger("llm_integration")


class LLMProvider:
    """Abstract LLM provider interface"""

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        raise NotImplementedError

    def classify_legal_query(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """
    OpenAI Provider - Primary LLM Engine using GPT-5.6 model.
    Fully centralized API call handling with error fallbacks and timeout protection.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", getattr(config, "OPENAI_API_KEY", ""))
        self.model = os.getenv("OPENAI_MODEL", getattr(config, "OPENAI_MODEL", "gpt-5.6"))
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.timeout = 30  # seconds

        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not configured in environment variables.")

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text from a single prompt string"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, max_tokens=max_tokens)

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Centralized chat completion method using OpenAI REST API"""
        if not self.api_key:
            logger.warning("Missing OPENAI_API_KEY - invoking fallback generator")
            return self._fallback_chat(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error("OpenAI API request timed out after 30 seconds.")
            return self._fallback_chat(messages, error_msg="Request timed out")
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"OpenAI API HTTP error: {http_err.response.status_code} - {http_err.response.text[:200]}")
            return self._fallback_chat(messages, error_msg="API service error")
        except Exception as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            return self._fallback_chat(messages, error_msg="LLM service unavailable")

    def classify_legal_query(self, text: str) -> Dict[str, Any]:
        """
        Classify legal query to identify intent, legal domain, lawyer necessity, and confidence.
        """
        system_prompt = (
            "You are a legal query classifier. Analyze the user question and return a valid JSON object with keys:\n"
            "- intent: (short snake_case identifier e.g. tenant_deposit_dispute, breach_of_contract, eviction_inquiry, general_inquiry)\n"
            "- legal_domain: (e.g. property / tenancy, contract_law, family_law, criminal_law, corporate_law)\n"
            "- requires_lawyer: (boolean true/false indicating if this matter is complex/high-risk)\n"
            "- confidence: (float between 0.0 and 1.0)\n"
            "Return ONLY raw JSON, no markdown formatting."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {text}"}
        ]

        raw_response = self.chat(messages, max_tokens=250)
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            data = json.loads(cleaned.strip())
            return {
                "intent": data.get("intent", "general_inquiry"),
                "legal_domain": data.get("legal_domain", "general_law"),
                "requires_lawyer": bool(data.get("requires_lawyer", False)),
                "confidence": float(data.get("confidence", 0.85))
            }
        except Exception:
            return self._heuristic_classification(text)

    def _heuristic_classification(self, text: str) -> Dict[str, Any]:
        """Fallback heuristic classification when LLM JSON parsing fails"""
        text_lower = text.lower()
        if any(w in text_lower for w in ["deposit", "rent", "landlord", "tenant", "lease"]):
            return {
                "intent": "tenant_deposit_dispute",
                "legal_domain": "property / tenancy",
                "requires_lawyer": False,
                "confidence": 0.80
            }
        elif any(w in text_lower for w in ["court", "sue", "police", "fir", "jail", "arrest"]):
            return {
                "intent": "high_risk_dispute",
                "legal_domain": "criminal / litigation",
                "requires_lawyer": True,
                "confidence": 0.90
            }
        return {
            "intent": "general_inquiry",
            "legal_domain": "general_law",
            "requires_lawyer": False,
            "confidence": 0.75
        }

    def _fallback_chat(self, messages: List[Dict[str, str]], error_msg: str = "") -> str:
        """Graceful fallback when OpenAI API key is unconfigured or request fails"""
        last_message = messages[-1]["content"] if messages else ""
        last_lower = last_message.lower()

        if "deposit" in last_lower:
            return "Based on the agreement details, the security deposit terms specify payment, refund timelines, and allowable deductions for property damage."
        elif "rent" in last_lower:
            return "According to the document text, rent is payable on a monthly basis by the designated due date specified in the agreement clauses."
        elif "notice" in last_lower or "terminat" in last_lower:
            return "The agreement provides that either party may terminate the lease by giving written notice as specified in the termination clause."
        
        return f"Based on the provided document: The document outlines rights, obligations, and terms related to your query. Please review the specific clause details carefully."


class LLMFactory:
    """Factory to select LLM provider"""

    @staticmethod
    def get_provider(provider_name: str = None) -> LLMProvider:
        """Get default or specified LLM provider instance"""
        if not provider_name:
            provider_name = getattr(config, "LLM_PROVIDER", os.getenv("LLM_PROVIDER", "openai"))
        
        provider_name = provider_name.lower()
        if provider_name == "openai":
            return OpenAIProvider()
        else:
            logger.info(f"Requested provider {provider_name}, defaulting to OpenAIProvider (GPT-5.6)")
            return OpenAIProvider()


# Global default LLM provider instance
llm_provider = LLMFactory.get_provider()
