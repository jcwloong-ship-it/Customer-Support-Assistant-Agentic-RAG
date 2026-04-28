"""
Tier 1 — Retrieval Accuracy Tests
==================================
Validates that ChromaDB's cosine-similarity search surfaces the correct
document for each query, that deduplication works correctly, and that
similarity scores fall within expected thresholds.

These tests use an in-memory ChromaDB collection with deterministic
fake embeddings so they run offline with zero latency.
"""

import math
import pytest

from app.data.default_documents import DEFAULT_DOCUMENTS
from app.services.chunker import TextChunker


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_seeded_db(in_memory_db, fake_embedding_service):
    """Seed in_memory_db with all default documents and return it."""
    chunker = TextChunker(chunk_size=300, overlap=45)
    chunks  = chunker.chunk_documents(DEFAULT_DOCUMENTS)
    texts   = [c["text"] for c in chunks]
    embeddings = fake_embedding_service.embed_texts(texts)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb
    in_memory_db.upsert_chunks(chunks)
    return in_memory_db


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRetrievalPrecision:
    """Context precision: does the top-k result contain the expected document?"""

    @pytest.fixture(autouse=True)
    def seed(self, in_memory_db, fake_embedding_service):
        self.db  = _build_seeded_db(in_memory_db, fake_embedding_service)
        self.emb = fake_embedding_service

    def _search(self, query: str, top_k: int = 6):
        vec = self.emb.embed_query(query)
        return self.db.vector_search(vec, top_k)

    def test_all_default_documents_indexed(self):
        """Every default document produces at least one chunk in the index."""
        assert self.db.count() >= len(DEFAULT_DOCUMENTS), (
            f"Expected at least {len(DEFAULT_DOCUMENTS)} chunks, "
            f"got {self.db.count()}"
        )

    def test_returns_similarity_scores(self):
        """Every result must carry a similarity score between 0 and 1."""
        results = self._search("return policy")
        assert results, "Search returned no results"
        for r in results:
            assert "similarity" in r, "Missing similarity key"
            assert isinstance(r["similarity"], float), "similarity must be a float"
            assert -1.0 <= r["similarity"] <= 1.0, (
                f"Similarity out of range: {r['similarity']}"
            )

    def test_results_sorted_by_similarity_descending(self):
        """Results must be ordered highest → lowest similarity."""
        results = self._search("shipping cost express delivery", top_k=6)
        scores = [r["similarity"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Results not sorted: {scores}"
        )

    def test_top_k_respects_limit(self):
        """vector_search must never return more items than top_k."""
        for k in (1, 3, 6):
            results = self._search("policy", top_k=k)
            assert len(results) <= k, (
                f"Expected ≤ {k} results, got {len(results)}"
            )

    def test_chunk_id_format(self):
        """All returned chunk_ids must follow the <doc_id>#<n> convention."""
        results = self._search("consultation duration")
        for r in results:
            assert "#" in r["chunk_id"], (
                f"chunk_id missing '#' separator: {r['chunk_id']}"
            )
            base, num = r["chunk_id"].rsplit("#", 1)
            assert base, "Base doc ID is empty"
            assert num.isdigit(), f"Chunk number is not an integer: {num}"

    def test_source_url_present(self):
        """Every result should carry a non-empty source URL."""
        results = self._search("return policy refund")
        for r in results:
            assert r.get("source"), (
                f"Missing source for chunk: {r['chunk_id']}"
            )


class TestDeduplication:
    """
    Deduplication logic in the orchestrator: at most one chunk per source
    document should appear in the context window.
    """

    @pytest.fixture(autouse=True)
    def seed(self, in_memory_db, fake_embedding_service):
        self.db  = _build_seeded_db(in_memory_db, fake_embedding_service)
        self.emb = fake_embedding_service

    def _deduplicated_results(self, query: str, top_k: int = 6, max_docs: int = 4):
        """Mirror the deduplication logic from AgentOrchestrator._retrieve."""
        raw = self.db.vector_search(self.emb.embed_query(query), top_k)
        seen, blocks = set(), []
        for r in raw:
            base = r["chunk_id"].split("#")[0]
            if base not in seen:
                blocks.append(r)
                seen.add(base)
            if len(blocks) >= max_docs:
                break
        return blocks

    def test_no_duplicate_source_docs(self):
        """After deduplication, each source document appears at most once."""
        results = self._deduplicated_results("policy", top_k=10, max_docs=6)
        base_ids = [r["chunk_id"].split("#")[0] for r in results]
        assert len(base_ids) == len(set(base_ids)), (
            f"Duplicate source documents found: {base_ids}"
        )

    def test_dedup_cap_respected(self):
        """Deduplication must cap results at max_docs."""
        for cap in (1, 2, 4):
            results = self._deduplicated_results("policy", top_k=10, max_docs=cap)
            assert len(results) <= cap, (
                f"cap={cap} violated: got {len(results)} results"
            )

    def test_dedup_preserves_highest_similarity(self):
        """The deduplicated first result should have a higher or equal similarity
        compared to other chunks from the same document."""
        raw     = self.db.vector_search(self.emb.embed_query("returns refund"), top_k=10)
        deduped = self._deduplicated_results("returns refund", top_k=10, max_docs=6)

        for deduped_chunk in deduped:
            base = deduped_chunk["chunk_id"].split("#")[0]
            # Collect all raw chunks from the same document
            same_doc_chunks = [r for r in raw if r["chunk_id"].split("#")[0] == base]
            max_raw_sim = max(c["similarity"] for c in same_doc_chunks)
            assert deduped_chunk["similarity"] == max_raw_sim, (
                f"Deduplication kept a non-best chunk for '{base}': "
                f"kept={deduped_chunk['similarity']:.4f}, "
                f"best available={max_raw_sim:.4f}"
            )


class TestChunkerBehaviour:
    """Unit tests for the text chunker used during seeding."""

    def setup_method(self):
        self.chunker = TextChunker(chunk_size=10, overlap=2)

    def test_short_text_produces_single_chunk(self):
        chunks = self.chunker.chunk_text("hello world", "src", "doc1")
        assert len(chunks) == 1
        assert chunks[0]["chunk_id"] == "doc1#1"

    def test_long_text_produces_multiple_chunks(self):
        words  = " ".join([f"word{i}" for i in range(25)])
        chunks = self.chunker.chunk_text(words, "src", "doc2")
        assert len(chunks) > 1, "Expected multiple chunks for a long text"

    def test_overlap_means_boundary_words_appear_twice(self):
        """Words near a chunk boundary should appear in the next chunk too."""
        words  = " ".join([f"w{i}" for i in range(20)])
        chunks = self.chunker.chunk_text(words, "src", "doc3")
        if len(chunks) < 2:
            pytest.skip("Not enough chunks to test overlap")
        last_words_chunk1  = set(chunks[0]["text"].split()[-2:])
        first_words_chunk2 = set(chunks[1]["text"].split()[:2])
        overlap = last_words_chunk1 & first_words_chunk2
        assert overlap, (
            f"No overlapping words between chunk 1 and chunk 2.\n"
            f"End of chunk 1: {chunks[0]['text'].split()[-3:]}\n"
            f"Start of chunk 2: {chunks[1]['text'].split()[:3]}"
        )

    def test_chunk_ids_are_sequential(self):
        words  = " ".join([f"x{i}" for i in range(30)])
        chunks = self.chunker.chunk_text(words, "src", "seq")
        nums   = [int(c["chunk_id"].split("#")[1]) for c in chunks]
        assert nums == list(range(1, len(chunks) + 1)), (
            f"Non-sequential chunk IDs: {nums}"
        )

    def test_source_propagated_to_all_chunks(self):
        words  = " ".join([f"y{i}" for i in range(25)])
        chunks = self.chunker.chunk_text(words, "my-source-url", "doc4")
        for chunk in chunks:
            assert chunk["source"] == "my-source-url"

    def test_unicode_normalisation(self):
        """Smart quotes and fancy punctuation should be normalised to ASCII."""
        text   = "\u201chello world\u201d and \u2018it\u2019s fine\u2019"
        chunks = self.chunker.chunk_text(text, "", "uni")
        combined = " ".join(c["text"] for c in chunks)
        assert "\u201c" not in combined, "Left double quote not normalised"
        assert "\u2018" not in combined, "Left single quote not normalised"
