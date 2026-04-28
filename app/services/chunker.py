"""Word-based text chunker with configurable size and overlap."""

import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

CHUNK_SIZE_WORDS = 300  # ~400 tokens
OVERLAP_WORDS    = 45   # ~15 % overlap ensures cross-boundary context is preserved


class TextChunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS):
        self.chunk_size = chunk_size
        self.overlap    = overlap

    def _clean(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        for old, new in [("\u201c", '"'), ("\u201d", '"'), ("\u2018", "'"), ("\u2019", "'")]:
            text = text.replace(old, new)
        return text

    def chunk_text(self, text: str, source: str, base_id: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks and return list of chunk dicts."""
        text  = self._clean(text)
        words = text.split()

        if len(words) <= self.chunk_size:
            return [{"chunk_id": f"{base_id}#1", "source": source, "text": text}]

        chunks, start, num = [], 0, 1
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunks.append({
                "chunk_id": f"{base_id}#{num}",
                "source":   source,
                "text":     " ".join(words[start:end]),
            })
            if end >= len(words):
                break
            start = end - self.overlap
            num  += 1

        logger.info(f"'{base_id}' → {len(chunks)} chunks")
        return chunks

    def chunk_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Chunk a list of document dicts, each with chunk_id, source, and text."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(
                self.chunk_text(doc["text"], doc.get("source", ""), doc["chunk_id"])
            )
        logger.info(f"{len(documents)} docs → {len(all_chunks)} total chunks")
        return all_chunks


chunker = TextChunker()
