"""
Centralized error handling for AgentTutor API.
Safe error responses — no internal details exposed to clients.
"""
from __future__ import annotations

import structlog
from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

logger = structlog.get_logger()


class AgentTutorError(Exception):
    """Base application error."""
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class NotFoundError(AgentTutorError):
    status_code = 404
    code = "not_found"


class ValidationError_(AgentTutorError):
    status_code = 422
    code = "validation_error"


class AuthorizationError(AgentTutorError):
    status_code = 403
    code = "forbidden"


class AuthenticationError(AgentTutorError):
    status_code = 401
    code = "unauthorized"


class LLMError(AgentTutorError):
    status_code = 502
    code = "llm_error"


class RateLimitError(AgentTutorError):
    status_code = 429
    code = "rate_limit_exceeded"


class UploadError(AgentTutorError):
    status_code = 400
    code = "upload_error"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AgentTutorError)
    def handle_app_error(err: AgentTutorError):
        logger.warning("application_error", code=err.code, message=err.message)
        return jsonify({"error": {"code": err.code, "message": err.message}}), err.status_code

    @app.errorhandler(ValidationError)
    def handle_pydantic_error(err: ValidationError):
        logger.warning("validation_error", errors=err.errors())
        return jsonify({
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": err.errors(),
            }
        }), 422

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        return jsonify({
            "error": {"code": str(err.code), "message": err.description}
        }), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        logger.error("unexpected_error", exc_info=True)
        return jsonify({
            "error": {"code": "internal_error", "message": "An unexpected error occurred"}
        }), 500

