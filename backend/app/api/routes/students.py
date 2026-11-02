"""Student progress routes."""
from flask import Blueprint, jsonify
from app.services.auth_service import require_auth
from app.models import StudentModel, Session

students_bp = Blueprint("students", __name__)


@students_bp.get("/me/progress")
def my_progress():
    user = require_auth()

    student_model = StudentModel.query.filter_by(user_id=user.id).first()
    if not student_model:
        return jsonify({
            "concept_scores": {},
            "misconceptions": [],
            "total_sessions": 0,
            "total_messages": 0,
            "course_states": {},
            "recent_sessions": [],
        })

    # Recent sessions
    recent = (
        Session.query
        .filter_by(student_id=user.id)
        .order_by(Session.created_at.desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "concept_scores": student_model.concept_scores,
        "misconceptions": student_model.misconceptions,
        "total_sessions": student_model.total_sessions,
        "total_messages": student_model.total_messages,
        "course_states": student_model.course_states,
        "recent_sessions": [
            {
                "id": s.id,
                "title": s.title,
                "session_type": s.session_type.value,
                "status": s.status.value,
                "concept": s.concept,
                "course_id": s.course_id,
                "created_at": s.created_at.isoformat(),
            }
            for s in recent
        ],
    })
