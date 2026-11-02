"""Document upload and management routes."""
from __future__ import annotations

import os
import uuid
from flask import Blueprint, jsonify, request
from app.errors import NotFoundError, UploadError
from app.extensions import db
from app.models import Course, CourseDocument, DocumentStatus
from app.services.auth_service import require_auth
from app.config import get_settings

documents_bp = Blueprint("documents", __name__)

cfg = get_settings()


@documents_bp.post("/<course_id>/documents")
def upload_document(course_id: str):
    user = require_auth()
    course = Course.query.get(course_id)
    if not course:
        raise NotFoundError(f"Course '{course_id}' not found")

    if "file" not in request.files:
        raise UploadError("No file in request")

    file = request.files["file"]
    if not file.filename:
        raise UploadError("No filename provided")

    original_filename = file.filename
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in cfg.allowed_extension_set:
        raise UploadError(f"File type '.{ext}' is not allowed. Accepted: {', '.join(cfg.allowed_extension_set)}")

    # Read and size-check
    content = file.read()
    if len(content) > cfg.max_upload_bytes:
        raise UploadError(f"File exceeds maximum size of {cfg.max_upload_size_mb}MB")

    # Save to disk
    safe_name = f"{uuid.uuid4()}.{ext}"
    upload_path = os.path.join(cfg.upload_dir, safe_name)
    os.makedirs(cfg.upload_dir, exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(content)

    doc = CourseDocument(
        course_id=course_id,
        uploaded_by=user.id,
        filename=safe_name,
        original_filename=original_filename,
        mime_type=file.content_type,
        file_size_bytes=len(content),
        status=DocumentStatus.pending,
    )
    db.session.add(doc)
    db.session.commit()

    # Trigger async processing (handled synchronously for now; background tasks in Phase 4)
    _schedule_ingestion(doc.id)

    return jsonify({"document": _serialize_doc(doc)}), 202


@documents_bp.get("/<course_id>/documents")
def list_documents(course_id: str):
    require_auth()
    course = Course.query.get(course_id)
    if not course:
        raise NotFoundError(f"Course '{course_id}' not found")

    docs = CourseDocument.query.filter_by(course_id=course_id).all()
    return jsonify({"documents": [_serialize_doc(d) for d in docs]})


@documents_bp.delete("/<course_id>/documents/<doc_id>")
def delete_document(course_id: str, doc_id: str):
    user = require_auth()
    doc = CourseDocument.query.filter_by(id=doc_id, course_id=course_id).first()
    if not doc:
        raise NotFoundError("Document not found")
    if str(doc.uploaded_by) != str(user.id) and user.role.value not in ("instructor", "admin"):
        from app.errors import AuthorizationError
        raise AuthorizationError("Not authorized to delete this document")

    # Remove file from disk
    file_path = os.path.join(cfg.upload_dir, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"message": "Document deleted"}), 200


def _schedule_ingestion(doc_id: str) -> None:
    """Trigger document ingestion. Runs synchronously in dev; async in prod."""
    try:
        from app.retrieval.ingestion import ingest_document
        ingest_document(doc_id)
    except Exception as e:
        import structlog
        structlog.get_logger().error("ingestion_schedule_failed", doc_id=doc_id, error=str(e))


def _serialize_doc(doc: CourseDocument) -> dict:
    return {
        "id": doc.id,
        "course_id": doc.course_id,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "status": doc.status.value,
        "error_message": doc.error_message,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat(),
    }
