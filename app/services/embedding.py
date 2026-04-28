"""OpenAI embedding service (text-embedding-3-small)."""

import logging
from typing import List

import openai

logger = logging.getLogger(__name__)


class EmbeddingService:
    MODEL      = "text-embedding-3-small"
    DIMENSIONS = 1536

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed a list of strings. Returns one vector per input."""
        if not texts:
            return []
        response = self.client.embeddings.create(model=self.MODEL, input=texts)
        logger.info(f"Embedded {len(texts)} texts")
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        return self.embed_texts([query])[0]
