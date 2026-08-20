"""
Vector Store Service - Abstraction layer for vector similarity search.
Provides Local Cosine Similarity Vector Store for SQLite development mode
and extensible interface for FAISS/ChromaDB/pgvector production setups.
"""
import math
from typing import List, Dict, Any, Optional
from backend.logging_config import get_logger

logger = get_logger("vector_store")


class VectorStore:
    """Abstract Base Class for Vector Stores"""

    def add_chunks(self, document_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        raise NotImplementedError

    def search(self, document_id: str, query_embedding: List[float], top_k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def delete_document_chunks(self, document_id: str) -> None:
        raise NotImplementedError


class LocalCosineVectorStore(VectorStore):
    """
    Local In-Memory / DB-backed Cosine Similarity Vector Store.
    Ideal for development environment without requiring native C++ library dependencies.
    """

    def __init__(self):
        # Internal memory map: document_id -> list of chunk records
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def add_chunks(self, document_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Store chunk texts, metadata, and embedding vectors for document_id"""
        if document_id not in self._store:
            self._store[document_id] = []

        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "chunk_id": f"chunk_{document_id}_{chunk.get('chunk_index', 0)}",
                "document_id": document_id,
                "chunk_index": chunk.get("chunk_index", 0),
                "text": chunk.get("text", ""),
                "section": chunk.get("section", "General"),
                "page": chunk.get("page", 1),
                "embedding": embedding
            }
            self._store[document_id].append(record)

        logger.info(f"VectorStore: Added {len(chunks)} vector chunks for document '{document_id}'.")

    def search(self, document_id: str, query_embedding: List[float], top_k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform cosine similarity search filtered strictly by document_id.
        Enforces tenant security isolation so document_id queries never return records from other documents.
        """
        if document_id not in self._store or not self._store[document_id]:
            return []

        document_records = self._store[document_id]
        scored_results = []

        for record in document_records:
            doc_embedding = record.get("embedding", [])
            score = self.cosine_similarity(query_embedding, doc_embedding)

            if score >= min_score:
                scored_results.append({
                    "chunk_id": record["chunk_id"],
                    "document_id": document_id,
                    "chunk_index": record["chunk_index"],
                    "text": record["text"],
                    "section": record["section"],
                    "page": record["page"],
                    "relevance_score": round(score, 4)
                })

        # Sort by relevance score descending
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_results[:top_k]

    def delete_document_chunks(self, document_id: str) -> None:
        """Remove all vector entries for document_id"""
        if document_id in self._store:
            del self._store[document_id]
            logger.info(f"VectorStore: Deleted chunks for document '{document_id}'.")

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate Cosine Similarity between vector A and vector B"""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# Global vector store instance
vector_store = LocalCosineVectorStore()
