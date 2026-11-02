"""JWT-based authentication service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import jwt
from flask import request

from app.config import get_settings
from app.errors import AuthenticationError
from app.models import User

cfg = get_settings()


def create_tokens(user_id: str) -> tuple[str, str]:
    """Create access and refresh JWTs."""
    now = datetime.now(timezone.utc)

    access_payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=cfg.jwt_access_token_expires_minutes),
    }
    refresh_payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=cfg.jwt_refresh_token_expires_days),
    }

    access_token = jwt.encode(access_payload, cfg.jwt_secret_key, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, cfg.jwt_secret_key, algorithm="HS256")
    return access_token, refresh_token


def decode_access_token(token: str) -> dict:
    """Decode and validate an access JWT. Raises AuthenticationError on failure."""
    try:
        payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {e}")


def require_auth() -> User:
    """Extract the authenticated user from the request. Raises on failure."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = auth_header[7:]
    payload = decode_access_token(token)
    user_id = payload["sub"]

    user = User.query.get(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return user


def optional_auth() -> User | None:
    """Like require_auth but returns None instead of raising when no token."""
    try:
        return require_auth()
    except AuthenticationError:
        return None
