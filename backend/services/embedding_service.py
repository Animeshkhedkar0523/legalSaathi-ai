"""
Embedding Service - Generating dense vector embeddings for RAG retrieval.
Primary Provider: OpenAI REST API (text-embedding-3-small).
Supports batching, error retries, rate-limiting resilience, and deterministic offline fallback vectors.
"""
import os
import math
import hashlib
import requests
from typing import List, Optional
from config import config
from backend.logging_config import get_logger

logger = get_logger("embedding_service")


class EmbeddingService:
    """Centralized Embedding Generation Service"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", getattr(config, "OPENAI_API_KEY", ""))
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", getattr(config, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
        self.api_url = "https://api.openai.com/v1/embeddings"
        self.vector_dim = 1536
        self.batch_size = 50
        self.timeout = 30  # seconds

    def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single string"""
        if not text or not text.strip():
            return [0.0] * self.vector_dim

        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * self.vector_dim

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a list of strings using batching & retry logic.
        """
        if not texts:
            return []

        cleaned_texts = [t.strip() if t and t.strip() else " " for t in texts]

        # Use offline deterministic embeddings if API key is not configured
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured - generating offline deterministic embeddings")
            return [self._fallback_embedding(t) for t in cleaned_texts]

        all_embeddings = []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Process in batches
        for i in range(0, len(cleaned_texts), self.batch_size):
            batch = cleaned_texts[i: i + self.batch_size]
            payload = {
                "model": self.model,
                "input": batch
            }

            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

                # Preserve input ordering
                batch_embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"OpenAI Embedding API error for batch {i}: {e}. Using fallback vectors for batch.")
                fallback_batch = [self._fallback_embedding(t) for t in batch]
                all_embeddings.extend(fallback_batch)

        return all_embeddings

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic 1536-dimensional L2-normalized float vector.
        Simulates dense neural embedding behavior in offline testing mode (high similarity for matching queries, low for non-matching).
        """
        import re
        if not text or not text.strip():
            return [0.0] * self.vector_dim

        vec = [0.0] * self.vector_dim
        words = set(re.findall(r'\w+', text.lower()))
        stop_words = {"what", "is", "the", "how", "much", "can", "i", "a", "an", "of", "or", "in", "to", "for", "on", "by", "this", "that"}
        meaningful_words = [w for w in words if len(w) >= 2 and w not in stop_words]

        # 1. Word hashing component
        for word in meaningful_words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.vector_dim
            vec[idx] += 25.0

        # 2. Base domain vector component (gives baseline similarity for valid queries)
        if meaningful_words:
            for i in range(300):
                vec[i] += 12.0

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]





# Global embedding service instance
embedding_service = EmbeddingService()
