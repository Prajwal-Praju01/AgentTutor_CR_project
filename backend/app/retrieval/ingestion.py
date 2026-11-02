"""
Document ingestion pipeline.
Accepts uploaded documents, extracts text, chunks it, generates embeddings,
and stores searchable chunks in the database.
"""
from __future__ import annotations

import os
import structlog

from app.config import get_settings
from app.extensions import db
from app.models import CourseDocument, DocumentChunk, DocumentStatus

logger = structlog.get_logger()
cfg = get_settings()


def ingest_document(doc_id: str) -> None:
    """
    Full ingestion pipeline for a single document.
    Updates document status in the database.
    """
    doc = CourseDocument.query.get(doc_id)
    if not doc:
        logger.error("ingest_document_not_found", doc_id=doc_id)
        return

    doc.status = DocumentStatus.processing
    db.session.commit()

    try:
        file_path = os.path.join(cfg.upload_dir, doc.filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: Extract text
        from app.retrieval.chunking import extract_and_chunk
        chunks_data = extract_and_chunk(file_path, doc.original_filename)

        if not chunks_data:
            raise ValueError("No text content extracted from document")

        # Step 2: Generate embeddings (if enabled)
        from app.retrieval.embeddings import EmbeddingProvider
        embedder = EmbeddingProvider()

        # Step 3: Store chunks
        for i, chunk in enumerate(chunks_data):
            embedding = None
            if cfg.enable_vector_search:
                try:
                    embedding = embedder.embed(chunk["content"])
                except Exception as e:
                    logger.warning("embedding_failed", chunk_index=i, error=str(e))

            db_chunk = DocumentChunk(
                document_id=doc.id,
                course_id=doc.course_id,
                content=chunk["content"],
                chunk_index=i,
                page_number=chunk.get("page_number"),
                section_title=chunk.get("section_title"),
                char_count=len(chunk["content"]),
                token_estimate=len(chunk["content"].split()),
                embedding_json=embedding,
            )
            db.session.add(db_chunk)

        doc.status = DocumentStatus.ready
        doc.page_count = chunks_data[-1].get("page_number") if chunks_data else None
        db.session.commit()

        logger.info(
            "document_ingested",
            doc_id=doc_id,
            chunk_count=len(chunks_data),
        )

    except Exception as e:
        logger.error("ingestion_failed", doc_id=doc_id, error=str(e))
        doc.status = DocumentStatus.failed
        doc.error_message = str(e)[:512]
        db.session.commit()

