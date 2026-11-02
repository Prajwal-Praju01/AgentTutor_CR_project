"""Course management routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field

from app.errors import NotFoundError
from app.extensions import db
from app.models import Course, Enrollment
from app.services.auth_service import require_auth

courses_bp = Blueprint("courses", __name__)


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=3, max_length=256)
    code: str = Field(min_length=2, max_length=32)
    description: str | None = None
    syllabus: str | None = None


class UpdateCourseRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    syllabus: str | None = None


@courses_bp.get("")
def list_courses():
    user = require_auth()
    # Students see enrolled courses; instructors/admins see all
    if user.role.value in ("instructor", "admin"):
        courses = Course.query.filter_by(is_active=True).all()
    else:
        enrollments = Enrollment.query.filter_by(user_id=user.id).all()
        course_ids = [e.course_id for e in enrollments]
        courses = Course.query.filter(
            Course.id.in_(course_ids), Course.is_active
        ).all()

    return jsonify({"courses": [_serialize_course(c) for c in courses]})


@courses_bp.post("")
def create_course():
    user = require_auth()
    data = CreateCourseRequest.model_validate(request.get_json(force=True) or {})

    if Course.query.filter_by(code=data.code).first():
        from app.errors import ValidationError_
        raise ValidationError_(f"Course code '{data.code}' already exists")

    course = Course(
        title=data.title,
        code=data.code,
        description=data.description,
        syllabus=data.syllabus,
        created_by=user.id,
    )
    db.session.add(course)
    # Auto-enroll the creator
    db.session.flush()
    enrollment = Enrollment(user_id=user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()

    return jsonify({"course": _serialize_course(course)}), 201


@courses_bp.get("/<course_id>")
def get_course(course_id: str):
    require_auth()
    course = _get_course_or_404(course_id)
    return jsonify({"course": _serialize_course(course)})


@courses_bp.patch("/<course_id>")
def update_course(course_id: str):
    require_auth()
    course = _get_course_or_404(course_id)
    data = UpdateCourseRequest.model_validate(request.get_json(force=True) or {})

    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.syllabus is not None:
        course.syllabus = data.syllabus

    db.session.commit()
    return jsonify({"course": _serialize_course(course)})


@courses_bp.post("/<course_id>/enroll")
def enroll(course_id: str):
    user = require_auth()
    course = _get_course_or_404(course_id)

    existing = Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first()
    if existing:
        return jsonify({"message": "Already enrolled"}), 200

    enrollment = Enrollment(user_id=user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Enrolled successfully"}), 201


def _get_course_or_404(course_id: str) -> Course:
    course = Course.query.get(course_id)
    if not course or not course.is_active:
        raise NotFoundError(f"Course '{course_id}' not found")
    return course


def _serialize_course(course: Course) -> dict:
    return {
        "id": course.id,
        "title": course.title,
        "code": course.code,
        "description": course.description,
        "syllabus": course.syllabus,
        "created_at": course.created_at.isoformat(),
        "document_count": len(course.documents) if course.documents else 0,
    }
