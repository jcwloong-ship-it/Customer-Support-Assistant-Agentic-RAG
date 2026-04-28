"""
Shared pytest fixtures for the Customer Support Assistant test suite.

All fixtures are designed to work without real API keys, OAuth tokens,
or an active network connection — external calls are mocked at the
boundary of each module under test.
"""

import sys
import os
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is on sys.path so `from app.xxx import yyy` works
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Minimal settings object ────────────────────────────────────────────────────

class _FakeSettings:
    ai_provider           = "openai"
    openai_api_key        = "sk-test-key"
    openai_chat_model     = "gpt-4o"
    openai_embed_model    = "text-embedding-3-small"
    anthropic_api_key     = ""
    anthropic_chat_model  = "claude-3-5-sonnet-20241022"
    google_calendar_email = "jcw.loong@gmail.com"
    temperature           = 0.1
    max_agent_iterations  = 5


@pytest.fixture
def fake_settings():
    return _FakeSettings()


# ── In-memory ChromaDB (no disk writes during tests) ──────────────────────────

@pytest.fixture
def in_memory_db():
    """
    A real ChromaDB collection backed by an ephemeral in-memory client.
    Avoids touching the project's persistent chroma_db/ directory.
    """
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    client     = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))
    collection = client.get_or_create_collection(
        name="test_rag_documents",
        metadata={"hnsw:space": "cosine"},
    )

    # Minimal VectorDatabase-compatible wrapper
    class _MemDB:
        def __init__(self, col):
            self._col = col

        def _get_collection(self):
            return self._col

        def upsert_chunks(self, chunks):
            self._col.upsert(
                ids       =[c["chunk_id"]  for c in chunks],
                embeddings=[c["embedding"] for c in chunks],
                documents =[c["text"]      for c in chunks],
                metadatas =[{"source": c.get("source", ""), "chunk_id": c["chunk_id"]}
                            for c in chunks],
            )
            return len(chunks)

        def vector_search(self, query_embedding, top_k=6):
            if self._col.count() == 0:
                return []
            results = self._col.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self._col.count()),
                include=["documents", "metadatas", "distances"],
            )
            return [
                {
                    "chunk_id":   meta.get("chunk_id", "unknown"),
                    "text":       doc,
                    "source":     meta.get("source", ""),
                    "similarity": round(1.0 - dist, 4),
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

        def count(self):
            return self._col.count()

        def clear(self):
            for item_id in self._col.get(include=[])["ids"]:
                self._col.delete(ids=[item_id])

    return _MemDB(collection)


# ── Deterministic fake embeddings (no OpenAI calls) ───────────────────────────

def _fake_embedding(seed: int = 0, dim: int = 8) -> List[float]:
    """Return a unit-length fake embedding seeded by an integer."""
    import math
    raw = [math.sin(seed + i) for i in range(dim)]
    norm = math.sqrt(sum(x ** 2 for x in raw)) or 1.0
    return [x / norm for x in raw]


@pytest.fixture
def fake_embedding_service():
    """EmbeddingService whose calls never hit OpenAI."""
    svc = MagicMock()
    svc.DIMENSIONS = 8

    call_count = {"n": 0}

    def _embed_texts(texts):
        results = []
        for t in texts:
            seed = sum(ord(c) for c in t[:20]) % 100
            results.append(_fake_embedding(seed))
            call_count["n"] += 1
        return results

    svc.embed_texts.side_effect = _embed_texts
    svc.embed_query.side_effect = lambda q: _embed_texts([q])[0]
    svc._call_count = call_count
    return svc
