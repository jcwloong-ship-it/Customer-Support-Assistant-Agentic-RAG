"""RAG pipeline — seed, add, and remove documents from ChromaDB + registry."""

import logging
from typing import Dict, List, Optional

from app.config.database import db
from app.config.kb_registry import delete_document, upsert_document
from app.data.default_documents import DEFAULT_DOCUMENTS
from app.services.chunker import chunker
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


def seed_knowledge_base(
    embedding_service: EmbeddingService,
    documents: Optional[List[Dict]] = None,
    force_reseed: bool = False,
) -> int:
    """
    Populate ChromaDB with embedded document chunks.

    Args:
        embedding_service: Initialised EmbeddingService.
        documents:         Docs to seed; falls back to DEFAULT_DOCUMENTS.
        force_reseed:      Clear the collection before seeding.

    Returns:
        Number of chunks upserted.
    """
    if force_reseed:
        db.clear()

    docs   = documents or DEFAULT_DOCUMENTS
    chunks = chunker.chunk_documents(docs)
    texts  = [c["text"] for c in chunks]
    embeddings = embedding_service.embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    count = db.upsert_chunks(chunks)

    # Track chunk counts per document for the registry
    chunk_counts: Dict[str, int] = {}
    for c in chunks:
        base = c["chunk_id"].split("#")[0]
        chunk_counts[base] = chunk_counts.get(base, 0) + 1

    for doc in docs:
        doc_id = doc["chunk_id"]
        upsert_document(
            doc_id=doc_id,
            title=_infer_title(doc["text"], doc_id),
            source=doc.get("source", ""),
            text=doc["text"],
            chunk_count=chunk_counts.get(doc_id, 1),
        )

    logger.info(f"Seeded {count} chunks from {len(docs)} documents")
    return count


def add_document(
    embedding_service: EmbeddingService,
    doc_id: str,
    title: str,
    source: str,
    text: str,
    tags: Optional[List[str]] = None,
) -> int:
    """Embed and store a single document, replacing any existing version."""
    doc    = {"chunk_id": doc_id, "source": source, "text": text}
    chunks = chunker.chunk_documents([doc])
    texts  = [c["text"] for c in chunks]
    embeddings = embedding_service.embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    count = db.upsert_chunks(chunks)
    upsert_document(
        doc_id=doc_id, title=title, source=source,
        text=text, chunk_count=count, tags=tags or [],
    )
    return count


def remove_document(doc_id: str) -> bool:
    """Delete a document and all its chunks from ChromaDB and the registry."""
    collection = db._get_collection()
    all_ids    = collection.get(include=[])["ids"]
    to_delete  = [i for i in all_ids if i == doc_id or i.startswith(f"{doc_id}#")]

    if to_delete:
        collection.delete(ids=to_delete)
        logger.info(f"Deleted {len(to_delete)} chunks for '{doc_id}'")

    return delete_document(doc_id)


def _infer_title(text: str, fallback: str) -> str:
    """Return the first non-empty line of text, truncated to 80 chars."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return fallback
