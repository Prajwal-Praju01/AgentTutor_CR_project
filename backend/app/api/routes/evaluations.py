"""Research evaluation result endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify

from app.errors import AuthorizationError, NotFoundError
from app.models import EvaluationRun, UserRole
from app.services.auth_service import require_auth

evaluations_bp = Blueprint("evaluations", __name__)


@evaluations_bp.get("/<evaluation_id>")
def get_evaluation(evaluation_id: str):
    """Return a persisted evaluation run to authorized research users."""
    user = require_auth()
    if user.role not in (UserRole.instructor, UserRole.admin):
        raise AuthorizationError("Evaluation results are restricted to instructors")

    evaluation = EvaluationRun.query.get(evaluation_id)
    if evaluation is None:
        raise NotFoundError("Evaluation run not found")

    return jsonify({
        "evaluation": {
            "id": evaluation.id,
            "experiment_name": evaluation.experiment_name,
            "condition": evaluation.condition,
            "model_version": evaluation.model_version,
            "prompt_version": evaluation.prompt_version,
            "dataset_name": evaluation.dataset_name,
            "sample_size": evaluation.sample_size,
            "config_snapshot": evaluation.config_snapshot,
            "results": evaluation.results,
            "status": evaluation.status,
            "notes": evaluation.notes,
            "created_at": evaluation.created_at.isoformat(),
            "updated_at": evaluation.updated_at.isoformat(),
        }
    })