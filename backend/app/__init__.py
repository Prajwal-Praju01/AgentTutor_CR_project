"""
AgentTutor application factory.
"""
from __future__ import annotations

import logging
import os

import structlog
from flask import Flask

from app.config import Settings, get_settings
from app.extensions import cors, db, limiter, migrate


def create_app(settings: Settings | None = None) -> Flask:
    """Application factory."""
    app = Flask(__name__, instance_relative_config=False)
    cfg = settings or get_settings()

    # ── Flask config ──────────────────────────────────────────────────────────
    app.config.update(
        SECRET_KEY=cfg.secret_key,
        SQLALCHEMY_DATABASE_URI=cfg.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": 300,
        },
        MAX_CONTENT_LENGTH=cfg.max_upload_bytes,
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    _configure_logging(cfg.log_level)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": cfg.cors_origin_list}})
    limiter.init_app(app)

    # ── Blueprints / Routes ───────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Error handlers ────────────────────────────────────────────────────────
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # ── Upload directory ──────────────────────────────────────────────────────
    os.makedirs(cfg.upload_dir, exist_ok=True)

    structlog.get_logger().info(
        "AgentTutor started",
        env=cfg.flask_env,
        llm_provider=cfg.llm_provider,
        vector_search=cfg.enable_vector_search,
    )

    return app


def _register_blueprints(app: Flask) -> None:
    from app.api.routes.health import health_bp
    from app.api.routes.auth import auth_bp
    from app.api.routes.courses import courses_bp
    from app.api.routes.sessions import sessions_bp
    from app.api.routes.students import students_bp
    from app.api.routes.documents import documents_bp
    from app.api.routes.evaluations import evaluations_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(courses_bp, url_prefix="/api/v1/courses")
    app.register_blueprint(sessions_bp, url_prefix="/api/v1/sessions")
    app.register_blueprint(students_bp, url_prefix="/api/v1/students")
    app.register_blueprint(documents_bp, url_prefix="/api/v1/courses")
    app.register_blueprint(evaluations_bp, url_prefix="/api/v1/evaluations")


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
