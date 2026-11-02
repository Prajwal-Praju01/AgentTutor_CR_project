"""
Retriever: semantic and keyword search over course document chunks.
Falls back to keyword search when vector search is disabled.
"""
from __future__ import annotations

import structlog
from sqlalchemy import text

from app.config import get_settings
from app.extensions import db
from app.models import DocumentChunk, CourseDocument, DocumentStatus

logger = structlog.get_logger()
cfg = get_settings()


class Retriever:
    """Course-scoped document retriever."""

    def search(
        self,
        course_id: str,
        query: str,
        top_k: int | None = None,
    ) -> list[dict]:
        k = top_k or cfg.retrieval_top_k

        if cfg.enable_vector_search:
            return self._vector_search(course_id, query, k)
        else:
            return self._keyword_search(course_id, query, k)

    def _keyword_search(self, course_id: str, query: str, k: int) -> list[dict]:
        """Simple case-insensitive keyword search."""
        keywords = [w.strip() for w in query.lower().split() if len(w.strip()) > 3]

        if not keywords:
            return []

        # Fetch all ready chunks for the course (bounded)
        chunks = (
            DocumentChunk.query
            .join(CourseDocument, DocumentChunk.document_id == CourseDocument.id)
            .filter(
                DocumentChunk.course_id == course_id,
                CourseDocument.status == DocumentStatus.ready,
            )
            .limit(500)
            .all()
        )

        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            score = sum(1.0 for kw in keywords if kw in content_lower) / len(keywords)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "content": c.content,
                "score": s,
                "document_name": c.document.original_filename if c.document else "Unknown",
                "page_number": c.page_number,
                "section_title": c.section_title,
                "chunk_id": c.id,
            }
            for s, c in scored[:k]
        ]

    def _vector_search(self, course_id: str, query: str, k: int) -> list[dict]:
        """
        pgvector cosine similarity search.
        Only available when ENABLE_VECTOR_SEARCH=true and embeddings are populated.
        """
        try:
            from app.retrieval.embeddings import EmbeddingProvider
            embedder = EmbeddingProvider()
            query_embedding = embedder.embed(query)

            # pgvector cosine distance query
            result = db.session.execute(
                text("""
                    SELECT dc.id, dc.content, dc.page_number, dc.section_title,
                           cd.original_filename,
                           (dc.embedding_json::vector <=> :q_vec::vector) AS distance
                    FROM document_chunks dc
                    JOIN course_documents cd ON dc.document_id = cd.id
                    WHERE dc.course_id = :course_id
                      AND cd.status = 'ready'
                    ORDER BY distance ASC
                    LIMIT :k
                """),
                {
                    "q_vec": str(query_embedding),
                    "course_id": course_id,
                    "k": k,
                },
            )
            rows = result.fetchall()
            return [
                {
                    "content": r.content,
                    "score": 1.0 - r.distance,
                    "document_name": r.original_filename,
                    "page_number": r.page_number,
                    "section_title": r.section_title,
                    "chunk_id": str(r.id),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("vector_search_failed", error=str(e), fallback="keyword")
            return self._keyword_search(course_id, query, k)

