"""Session and message routes."""
from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field

from app.errors import NotFoundError, AuthorizationError
from app.extensions import db
from app.models import (
    Session, Message, MessageRole, SessionType, SessionStatus,
    DebuggingTask, TaskStatus
)
from app.services.auth_service import require_auth
from app.tutoring.orchestrator import TutoringOrchestrator

sessions_bp = Blueprint("sessions", __name__)


class CreateSessionRequest(BaseModel):
    course_id: str | None = None
    session_type: str = "tutoring"
    title: str | None = None
    concept: str | None = None
    # For debugging sessions
    buggy_code: str | None = None
    language: str = "python"
    description: str | None = None
    expected_behavior: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


@sessions_bp.post("")
def create_session():
    user = require_auth()
    data = CreateSessionRequest.model_validate(request.get_json(force=True) or {})

    session_type = SessionType(data.session_type)
    session = Session(
        student_id=user.id,
        course_id=data.course_id,
        session_type=session_type,
        title=data.title,
        concept=data.concept,
        status=SessionStatus.active,
    )
    db.session.add(session)
    db.session.flush()

    if session_type == SessionType.debugging:
        if not data.buggy_code or not data.description:
            from app.errors import ValidationError_
            raise ValidationError_("buggy_code and description are required for debugging sessions")
        task = DebuggingTask(
            session_id=session.id,
            title=data.title or "Debugging Task",
            description=data.description,
            buggy_code=data.buggy_code,
            language=data.language,
            expected_behavior=data.expected_behavior,
            status=TaskStatus.pending,
        )
        db.session.add(task)

    db.session.commit()
    return jsonify({"session": _serialize_session(session)}), 201


@sessions_bp.get("/<session_id>")
def get_session(session_id: str):
    user = require_auth()
    session = _get_session_or_404(session_id, user.id)
    return jsonify({"session": _serialize_session(session)})


@sessions_bp.get("/<session_id>/history")
def get_history(session_id: str):
    user = require_auth()
    session = _get_session_or_404(session_id, user.id)
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    return jsonify({
        "session": _serialize_session(session),
        "messages": [_serialize_message(m) for m in messages],
    })


@sessions_bp.post("/<session_id>/messages")
def send_message(session_id: str):
    user = require_auth()
    session = _get_session_or_404(session_id, user.id)

    if session.status != SessionStatus.active:
        from app.errors import ValidationError_
        raise ValidationError_("Session is not active")

    data = SendMessageRequest.model_validate(request.get_json(force=True) or {})

    # Persist student message
    student_msg = Message(
        session_id=session_id,
        role=MessageRole.student,
        content=data.content,
    )
    db.session.add(student_msg)
    db.session.flush()

    # Run orchestrator
    orchestrator = TutoringOrchestrator()
    response = orchestrator.handle_message(
        session=session,
        student_message=data.content,
        user=user,
    )

    # Persist tutor response
    tutor_msg = Message(
        session_id=session_id,
        role=MessageRole.tutor,
        content=response.content,
        msg_metadata={
            "understanding_level": response.understanding_level,
            "hint_depth": response.hint_depth,
            "assessment": response.assessment,
            "citations": response.citations,
            "next_question": response.next_question,
        },
        token_count=response.token_count,
    )
    db.session.add(tutor_msg)
    db.session.commit()

    return jsonify({
        "student_message": _serialize_message(student_msg),
        "tutor_message": _serialize_message(tutor_msg),
        "assessment": response.assessment,
    })


@sessions_bp.get("/<session_id>/states")
def get_states(session_id: str):
    user = require_auth()
    session = _get_session_or_404(session_id, user.id)

    if session.session_type != SessionType.debugging or not session.debugging_task:
        return jsonify({"states": []})

    states = session.debugging_task.learning_states
    return jsonify({
        "states": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "order_index": s.order_index,
                "status": s.status.value,
                "resolution_evidence": s.resolution_evidence,
            }
            for s in sorted(states, key=lambda x: x.order_index)
        ]
    })


@sessions_bp.patch("/<session_id>/end")
def end_session(session_id: str):
    user = require_auth()
    session = _get_session_or_404(session_id, user.id)
    session.status = SessionStatus.completed
    session.ended_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"session": _serialize_session(session)})


def _get_session_or_404(session_id: str, user_id: str) -> Session:
    session = Session.query.get(session_id)
    if not session:
        raise NotFoundError(f"Session '{session_id}' not found")
    if str(session.student_id) != str(user_id):
        raise AuthorizationError("Not authorized to access this session")
    return session


def _serialize_session(session: Session) -> dict:
    return {
        "id": session.id,
        "student_id": session.student_id,
        "course_id": session.course_id,
        "session_type": session.session_type.value,
        "status": session.status.value,
        "title": session.title,
        "concept": session.concept,
        "created_at": session.created_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
    }


def _serialize_message(msg: Message) -> dict:
    return {
        "id": msg.id,
        "session_id": msg.session_id,
        "role": msg.role.value,
        "content": msg.content,
        "metadata": msg.msg_metadata,
        "created_at": msg.created_at.isoformat(),
    }
