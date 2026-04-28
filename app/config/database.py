"""ChromaDB local vector database wrapper."""

import logging
import os
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")


class VectorDatabase:
    COLLECTION_NAME = "rag_documents"

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"ChromaDB initialised at: {CHROMA_PATH}")
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"Collection '{self.COLLECTION_NAME}' ready "
                f"({self._collection.count()} docs)"
            )
        return self._collection

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Insert or update document chunks. Each chunk must have: chunk_id, text, source, embedding."""
        collection = self._get_collection()
        collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=[c["embedding"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c.get("source", ""), "chunk_id": c["chunk_id"]} for c in chunks],
        )
        logger.info(f"Upserted {len(chunks)} chunks")
        return len(chunks)

    def vector_search(self, query_embedding: List[float], top_k: int = 6) -> List[Dict[str, Any]]:
        """Cosine-similarity search. Returns list of {chunk_id, text, source, similarity}."""
        collection = self._get_collection()

        if collection.count() == 0:
            logger.warning("Collection is empty — seed documents first.")
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        return [
            {
                "chunk_id":  meta.get("chunk_id", "unknown"),
                "text":      doc,
                "source":    meta.get("source", ""),
                "similarity": round(1.0 - dist, 4),
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def count(self) -> int:
        return self._get_collection().count()

    def clear(self):
        """Delete and recreate the collection."""
        client = self._get_client()
        try:
            client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None
        self._get_collection()


db = VectorDatabase()
