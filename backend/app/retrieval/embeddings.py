"""
Embedding provider adapter.
Supports: openai | sentence_transformers | mock
"""
from __future__ import annotations

from app.config import get_settings

cfg = get_settings()


class EmbeddingProvider:
    """Unified embedding interface."""

    def __init__(self):
        self._backend = _build_backend()

    def embed(self, text: str) -> list[float]:
        return self._backend.embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._backend.embed_batch(texts)


class MockEmbeddingBackend:
    """Deterministic mock returning zero vectors."""
    DIM = 1536

    def embed(self, text: str) -> list[float]:
        # Simple hash-based pseudo-embedding for testing
        import hashlib
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(h >> i & 0xFF) / 255.0 for i in range(self.DIM)]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class OpenAIEmbeddingBackend:
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=cfg.embedding_api_key or cfg.llm_api_key)
        self._model = cfg.embedding_model

    def embed(self, text: str) -> list[float]:
        resp = self._client.embeddings.create(input=text, model=self._model)
        return resp.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(input=texts, model=self._model)
        return [r.embedding for r in resp.data]


class SentenceTransformerBackend:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(cfg.embedding_model)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts).tolist()


def _build_backend():
    if cfg.embedding_provider == "openai":
        return OpenAIEmbeddingBackend()
    elif cfg.embedding_provider == "sentence_transformers":
        return SentenceTransformerBackend()
    else:
        return MockEmbeddingBackend()

