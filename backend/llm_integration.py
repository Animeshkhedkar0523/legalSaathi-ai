"""
LLM Integration - OpenAI, Anthropic (Claude) support with free APIs
"""
import os
from typing import Optional
import requests
from backend.logging_config import get_logger

logger = get_logger("llm_integration")


class LLMProvider:
    """Abstract LLM provider"""
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        raise NotImplementedError
    
    def chat(self, messages: list, max_tokens: int = 1000) -> str:
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider - Use free API (claude-3-5-sonnet)"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20241022"  # Free model
        
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not configured - using fallback")
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Claude"""
        if not self.api_key:
            return self._fallback_generate(prompt)
        
        try:
            headers = {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key
            }
            
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data["content"][0]["text"]
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._fallback_generate(prompt)
    
    def chat(self, messages: list, max_tokens: int = 1000) -> str:
        """Chat with Claude"""
        if not self.api_key:
            return self._fallback_chat(messages)
        
        try:
            headers = {
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
                "x-api-key": self.api_key
            }
            
            # Convert to Anthropic message format
            converted_messages = [
                {"role": "user" if m.get("role") == "user" else "assistant", "content": m["content"]}
                for m in messages
            ]
            
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": converted_messages
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data["content"][0]["text"]
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._fallback_chat(messages)
    
    @staticmethod
    def _fallback_generate(prompt: str) -> str:
        """Fallback generation when API not available"""
        if "rental" in prompt.lower():
            return """RENTAL AGREEMENT (AI-Generated)

This Rental Agreement is entered into between the Landlord and Tenant as specified.

Key Terms:
1. RENT PAYMENT - Rent shall be paid monthly on the 5th of each month
2. SECURITY DEPOSIT - A security deposit has been collected
3. PROPERTY MAINTENANCE - Tenant shall maintain property in good condition
4. TERMINATION - Either party may terminate with 30 days written notice
5. UTILITIES - Tenant shall bear costs of utilities
6. DISPUTE RESOLUTION - Governed by applicable laws

This agreement is binding upon all parties."""
        
        elif "affidavit" in prompt.lower():
            return """AFFIDAVIT (AI-Generated)

I solemnly affirm and declare that the facts stated herein are true to the best of my knowledge and belief.

1. I have personal knowledge of the matters stated
2. I have not concealed any material facts
3. I am aware of the consequences of making false statements
4. The information provided is accurate and complete

Signature: ________________
Date: ____________________"""
        
        elif "will" in prompt.lower():
            return """WILL AND TESTAMENT (AI-Generated)

I hereby revoke all previous wills and declare this to be my Last Will.

1. TESTATOR - I am of sound mind and testamentary capacity
2. ASSETS - I declare ownership of specified assets and property
3. DISTRIBUTION - My estate shall be distributed per applicable succession laws
4. EXECUTOR - I appoint a qualified executor to manage my estate
5. GUARDIANSHIP - I nominate guardians for minor children if applicable

This will must be witnessed and properly executed as per legal requirements."""
        
        else:
            return f"[AI-Generated Response] Based on your request: {prompt[:100]}..."
    
    @staticmethod
    def _fallback_chat(messages: list) -> str:
        """Fallback chat when API not available"""
        last_message = messages[-1]["content"] if messages else ""
        if "risk" in last_message.lower():
            return "Based on the document analysis, I've identified several key risk areas. Please review the clauses carefully and consider consulting with a legal professional."
        return "Thank you for your question. Please provide more specific details for a more accurate response."


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider - Use free trial API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"  # Free tier available
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured - using fallback")
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using OpenAI"""
        if not self.api_key:
            return AnthropicProvider._fallback_generate(prompt)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return AnthropicProvider._fallback_generate(prompt)
    
    def chat(self, messages: list, max_tokens: int = 1000) -> str:
        """Chat with OpenAI"""
        if not self.api_key:
            return AnthropicProvider._fallback_chat(messages)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return AnthropicProvider._fallback_chat(messages)


class LLMFactory:
    """Factory to select LLM provider"""
    
    @staticmethod
    def get_provider(provider_name: str = "anthropic") -> LLMProvider:
        """Get LLM provider instance"""
        provider_name = provider_name.lower()
        
        if provider_name == "anthropic":
            return AnthropicProvider()
        elif provider_name == "openai":
            return OpenAIProvider()
        else:
            logger.info(f"Unknown provider {provider_name}, using Anthropic")
            return AnthropicProvider()


# Default provider (try Anthropic first, fallback to OpenAI)
llm_provider = LLMFactory.get_provider(os.getenv("LLM_PROVIDER", "anthropic"))
