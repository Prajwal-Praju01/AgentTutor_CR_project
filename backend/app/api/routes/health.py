"""Health check endpoint."""
from flask import Blueprint, jsonify
from app.extensions import db
import sqlalchemy as sa

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Basic liveness check."""
    db_ok = False
    db_error = None
    try:
        db.session.execute(sa.text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    status = "ok" if db_ok else "degraded"
    return jsonify({
        "status": status,
        "version": "1.0.0",
        "components": {
            "database": "ok" if db_ok else f"error: {db_error}",
        },
    }), 200 if db_ok else 503

