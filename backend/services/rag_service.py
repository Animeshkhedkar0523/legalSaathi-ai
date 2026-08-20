"""
RAG Service - Orchestrates document indexing, re-indexing, embedding generation,
vector storage, and security-isolated semantic retrieval.
"""
import json
from typing import List, Dict, Any, Optional
from config import config
from backend.logging_config import get_logger
from backend.database import SessionLocal, DocumentModel, DocumentChunkModel
from backend.services.document_chunker import document_chunker
from backend.services.embedding_service import embedding_service
from backend.services.vector_store import vector_store

logger = get_logger("rag_service")


class RAGService:
    """Production RAG Pipeline Orchestrator"""

    def __init__(self):
        self.top_k = getattr(config, "RAG_TOP_K", 5)
        self.similarity_threshold = getattr(config, "RAG_SIMILARITY_THRESHOLD", 0.70)

    def index_document(self, document_id: str) -> bool:
        """
        Index a document into the RAG pipeline:
        Text -> Clean -> Chunk -> Embed -> Store DB & Vector Store -> Mark INDEXED
        """
        session = SessionLocal()
        try:
            doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if not doc:
                logger.error(f"RAG Indexing Failed: Document '{document_id}' not found.")
                return False

            doc.document_status = "INDEXING"
            session.commit()

            text = doc.content
            if not text or not text.strip():
                doc.document_status = "INDEXED"
                session.commit()
                return True

            # 1. Chunk document
            chunks = document_chunker.chunk_document(text, document_id=document_id)
            if not chunks:
                doc.document_status = "INDEXED"
                session.commit()
                return True

            # 2. Generate embeddings
            chunk_texts = [c["text"] for c in chunks]
            embeddings = embedding_service.generate_embeddings(chunk_texts)

            # 3. Clean existing database chunks & vector store records
            session.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).delete()
            vector_store.delete_document_chunks(document_id)

            # 4. Insert new DocumentChunkModel records into DB
            db_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                db_chunk = DocumentChunkModel(
                    document_id=document_id,
                    chunk_index=chunk["chunk_index"],
                    text=chunk["text"],
                    section=chunk.get("section", "General"),
                    metadata_json=json.dumps({"page": chunk.get("page", 1)}),
                    embedding_json=json.dumps(embedding)
                )
                db_chunks.append(db_chunk)

            session.add_all(db_chunks)
            doc.document_status = "INDEXED"
            session.commit()

            # 5. Add to vector store index
            vector_store.add_chunks(document_id, chunks, embeddings)
            logger.info(f"RAG Indexing Complete: Document '{document_id}' successfully indexed into {len(chunks)} chunks.")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"RAG Indexing Error for document '{document_id}': {e}")
            try:
                doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                if doc:
                    doc.document_status = "FAILED"
                    session.commit()
            except Exception:
                pass
            return False
        finally:
            session.close()

    def reindex_document(self, document_id: str) -> bool:
        """Invalidate existing vector chunks and re-index document"""
        logger.info(f"Re-indexing document '{document_id}'...")
        vector_store.delete_document_chunks(document_id)
        return self.index_document(document_id)

    def retrieve_relevant_chunks(
        self,
        document_id: str,
        query: str,
        user_id: str,
        top_k: int = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic vector retrieval filtered strictly by document_id and authorized user_id.
        User A can NEVER retrieve User B's document chunks.
        """
        top_k = top_k or self.top_k
        similarity_threshold = similarity_threshold or self.similarity_threshold

        session = SessionLocal()
        try:
            # Security Ownership Check
            doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if not doc:
                logger.warning(f"RAG Retrieval Warning: Document '{document_id}' does not exist.")
                return []

            if doc.user_id != user_id:
                logger.error(f"RAG Security Rejection: User '{user_id}' attempted to access document '{document_id}' owned by user '{doc.user_id}'.")
                raise ValueError("Unauthorized document access")

            # Auto-index if not yet indexed in vector store
            vec_results = vector_store.search(document_id, [], top_k=1)
            if not vec_results:
                # Load chunks from DB into vector store if present, or reindex
                db_chunks = session.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).all()
                if db_chunks:
                    chunks = []
                    embeddings = []
                    for c in db_chunks:
                        chunks.append({
                            "chunk_index": c.chunk_index,
                            "text": c.text,
                            "section": c.section,
                            "page": 1
                        })
                        embeddings.append(json.loads(c.embedding_json) if c.embedding_json else [])
                    vector_store.add_chunks(document_id, chunks, embeddings)
                else:
                    self.index_document(document_id)

            # Generate Query Embedding & Vector Search
            query_embedding = embedding_service.generate_embedding(query)
            results = vector_store.search(
                document_id=document_id,
                query_embedding=query_embedding,
                top_k=top_k,
                min_score=0.0
            )

            if results:
                logger.info(f"RAG Debug: Query='{query}', Top Score={results[0]['relevance_score']}, Required Threshold={similarity_threshold}")
                results = [r for r in results if r['relevance_score'] >= similarity_threshold]

            logger.info(f"RAG Retrieval: Found {len(results)} relevant chunks for query in document '{document_id}'.")
            return results

        finally:
            session.close()


# Global RAG service instance
rag_service = RAGService()
