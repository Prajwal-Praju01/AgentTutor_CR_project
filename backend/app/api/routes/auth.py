"""Authentication routes."""
from __future__ import annotations

import bcrypt
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field

from app.errors import AuthenticationError, ValidationError_
from app.extensions import db
from app.models import User, UserRole, StudentModel
from app.services.auth_service import create_tokens, require_auth

auth_bp = Blueprint("auth", __name__)


class RegisterRequest(BaseModel):
    email: str
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


@auth_bp.post("/register")
def register():
    data = RegisterRequest.model_validate(request.get_json(force=True) or {})

    if User.query.filter_by(email=data.email).first():
        raise ValidationError_("Email already registered")
    if User.query.filter_by(username=data.username).first():
        raise ValidationError_("Username already taken")

    pw_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = User(
        email=data.email,
        username=data.username,
        password_hash=pw_hash,
        display_name=data.display_name or data.username,
        role=UserRole.student,
    )
    db.session.add(user)
    db.session.flush()

    # Initialize empty student model
    student_model = StudentModel(user_id=user.id)
    db.session.add(student_model)
    db.session.commit()

    access_token, refresh_token = create_tokens(user.id)
    return jsonify({
        "user": _serialize_user(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


@auth_bp.post("/login")
def login():
    data = LoginRequest.model_validate(request.get_json(force=True) or {})

    user = User.query.filter_by(email=data.email).first()
    if not user or not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        raise AuthenticationError("Invalid credentials")
    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    access_token, refresh_token = create_tokens(user.id)
    return jsonify({
        "user": _serialize_user(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


@auth_bp.get("/me")
def me():
    user = require_auth()
    return jsonify({"user": _serialize_user(user)})


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
        "created_at": user.created_at.isoformat(),
    }
