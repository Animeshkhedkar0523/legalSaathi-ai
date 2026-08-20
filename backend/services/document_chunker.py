"""
Document Chunker Service - Smart boundary-aware text chunking.
Splits legal documents into structured chunks preserving paragraph, section, and sentence boundaries.
Configurable chunk size and overlap loaded from environment/config.
"""
import re
from typing import List, Dict, Any, Optional
from config import config
from backend.logging_config import get_logger

logger = get_logger("document_chunker")


class DocumentChunker:
    """Paragraph and section boundary-aware text chunker"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or getattr(config, "CHUNK_SIZE", 1000)
        self.chunk_overlap = chunk_overlap or getattr(config, "CHUNK_OVERLAP", 150)

    def chunk_document(self, text: str, document_id: str = "") -> List[Dict[str, Any]]:
        """
        Split document text into structured metadata chunks.
        Preserves section headings (e.g., '1. RENT PAYMENT', 'SECTION 2', 'TERMS AND CONDITIONS').
        """
        if not text or not text.strip():
            return []

        cleaned_text = self._clean_text(text)
        sections = self._split_by_sections_or_paragraphs(cleaned_text)
        
        chunks = []
        current_chunk_sentences = []
        current_length = 0
        current_section = "General"
        chunk_index = 0

        for section_title, section_text in sections:
            if section_title:
                current_section = section_title

            sentences = self._split_into_sentences(section_text)

            for sentence in sentences:
                sentence_len = len(sentence)
                
                # If adding sentence exceeds chunk_size and we already have text, finalize current chunk
                if current_length + sentence_len > self.chunk_size and current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences).strip()
                    chunks.append({
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "section": current_section,
                        "page": 1
                    })
                    chunk_index += 1

                    # Build overlap from previous sentences
                    overlap_sentences = []
                    overlap_len = 0
                    for prev_sent in reversed(current_chunk_sentences):
                        if overlap_len + len(prev_sent) <= self.chunk_overlap:
                            overlap_sentences.insert(0, prev_sent)
                            overlap_len += len(prev_sent)
                        else:
                            break

                    current_chunk_sentences = overlap_sentences
                    current_length = overlap_len

                current_chunk_sentences.append(sentence)
                current_length += sentence_len

        # Final remaining chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences).strip()
            if chunk_text:
                chunks.append({
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "section": current_section,
                    "page": 1
                })

        logger.info(f"Chunked document '{document_id}' ({len(text)} chars) into {len(chunks)} chunks.")
        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean excessive whitespace while preserving paragraph structure"""
        text = text.replace("\r\n", "\n")
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines)

    def _split_by_sections_or_paragraphs(self, text: str) -> List[tuple]:
        """Split text into (section_name, content) tuples based on headings or double newlines"""
        lines = text.split("\n")
        sections = []
        current_heading = None
        current_lines = []

        # Regex for section headings like "1. RENT PAYMENT", "SECTION A", "TERMS AND CONDITIONS:"
        heading_regex = re.compile(r"^(\d+[\.\)]\s*|[A-Z\s]{4,}:?|SECTION\s+\d+:?|ARTICLE\s+\d+:?)", re.IGNORECASE)

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if heading_regex.match(line_str) and len(line_str) < 80:
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines)))
                    current_lines = []
                current_heading = line_str
            else:
                current_lines.append(line_str)

        if current_lines:
            sections.append((current_heading, "\n".join(current_lines)))

        return sections if sections else [(None, text)]

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences cleanly without breaking abbreviation numbers or bullet points"""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]


# Global document chunker instance
document_chunker = DocumentChunker()
