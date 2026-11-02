"""
SQLAlchemy database models for AgentTutor.
All tables use UUID primary keys, created_at / updated_at timestamps,
proper foreign keys, and indexes on common query patterns.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.extensions import db


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uuid():
    return str(uuid.uuid4())

def _now():
    return datetime.now(timezone.utc)

# Cross-database JSON type — uses JSONB on PostgreSQL, JSON elsewhere
JSONB = JSON

# Cross-database UUID column — String(36) works on both SQLite and PostgreSQL
def UUIDCol(primary_key=False, **kwargs):
    """UUID column that works on SQLite (tests) and PostgreSQL (production)."""
    return Column(String(36), primary_key=primary_key, default=_uuid, **kwargs)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class SessionType(str, enum.Enum):
    tutoring = "tutoring"
    debugging = "debugging"


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"


class MessageRole(str, enum.Enum):
    student = "student"
    tutor = "tutor"
    system = "system"


class UnderstandingLevel(int, enum.Enum):
    confused = 0
    beginner = 1
    developing = 2
    mastered = 3


class HintDepth(int, enum.Enum):
    conceptual = 1
    directional = 2
    partial_reveal = 3
    full_solution = 4


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class QuestionType(str, enum.Enum):
    root = "root"
    child = "child"
    sibling = "sibling"


class VerifierVerdict(str, enum.Enum):
    correct = "correct"
    partially_correct = "partially_correct"
    incorrect = "incorrect"
    uncertain = "uncertain"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    resolved = "resolved"
    unresolved = "unresolved"


class FixStatus(str, enum.Enum):
    proposed = "proposed"
    syntax_valid = "syntax_valid"
    tests_passed = "tests_passed"
    tests_failed = "tests_failed"
    unverified = "unverified"


# ── Users ─────────────────────────────────────────────────────────────────────

class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(320), unique=True, nullable=False, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    display_name = Column(String(128), nullable=True)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="student", cascade="all, delete-orphan")
    student_model = relationship("StudentModel", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.username}>"


# ── Courses ───────────────────────────────────────────────────────────────────

class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(256), nullable=False)
    code = Column(String(32), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    syllabus = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    documents = relationship("CourseDocument", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="course")


class Enrollment(TimestampMixin, db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


# ── Documents & Chunks ────────────────────────────────────────────────────────

class CourseDocument(TimestampMixin, db.Model):
    __tablename__ = "course_documents"

    id = Column(String(36), primary_key=True, default=_uuid)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    filename = Column(String(256), nullable=False)
    original_filename = Column(String(256), nullable=False)
    mime_type = Column(String(128), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.pending, nullable=False)
    error_message = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    doc_metadata = Column("doc_metadata", JSONB, nullable=True)

    course = relationship("Course", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(TimestampMixin, db.Model):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=_uuid)
    document_id = Column(String(36), ForeignKey("course_documents.id"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(512), nullable=True)
    char_count = Column(Integer, nullable=True)
    token_estimate = Column(Integer, nullable=True)
    # Embedding stored as JSON array when pgvector is not available
    embedding_json = Column(JSONB, nullable=True)

    document = relationship("CourseDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunk_document_index", "document_id", "chunk_index"),
        Index("ix_chunk_course", "course_id"),
    )


# ── Sessions & Messages ───────────────────────────────────────────────────────

class Session(TimestampMixin, db.Model):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True, index=True)
    session_type = Column(Enum(SessionType), default=SessionType.tutoring, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.active, nullable=False)
    title = Column(String(256), nullable=True)
    concept = Column(String(256), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("User", back_populates="sessions")
    course = relationship("Course", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    student_model_snapshot = relationship("StudentModelSnapshot", back_populates="session", cascade="all, delete-orphan")
    debugging_task = relationship("DebuggingTask", back_populates="session", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_session_student_status", "student_id", "status"),
    )


class Message(TimestampMixin, db.Model):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    # Structured metadata: assessment, hint depth, citations, etc.
    msg_metadata = Column("metadata", JSONB, nullable=True)
    token_count = Column(Integer, nullable=True)

    session = relationship("Session", back_populates="messages")


# ── Student Model ─────────────────────────────────────────────────────────────

class StudentModel(TimestampMixin, db.Model):
    """Persistent per-student learning profile across all courses."""
    __tablename__ = "student_models"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # Aggregate understanding scores per concept (JSON: {concept: score})
    concept_scores = Column(JSONB, default=dict, nullable=False)
    # Identified misconceptions (JSON: list of {concept, description, count})
    misconceptions = Column(JSONB, default=list, nullable=False)
    # Session-level stats
    total_sessions = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    # Per-course learning states
    course_states = Column(JSONB, default=dict, nullable=False)

    user = relationship("User", back_populates="student_model")
    snapshots = relationship("StudentModelSnapshot", back_populates="student_model", cascade="all, delete-orphan")


class StudentModelSnapshot(TimestampMixin, db.Model):
    """Point-in-time snapshot of student model state after each session message."""
    __tablename__ = "student_model_snapshots"

    id = Column(String(36), primary_key=True, default=_uuid)
    student_model_id = Column(String(36), ForeignKey("student_models.id"), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)

    understanding_level = Column(Integer, nullable=False)  # 0-3
    hint_depth = Column(Integer, nullable=False)  # 1-4
    concept = Column(String(256), nullable=True)
    justification = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    identified_misconceptions = Column(JSONB, default=list)

    student_model = relationship("StudentModel", back_populates="snapshots")
    session = relationship("Session", back_populates="student_model_snapshot")


# ── Debugging ─────────────────────────────────────────────────────────────────

class DebuggingTask(TimestampMixin, db.Model):
    """Root debugging task linked to a session."""
    __tablename__ = "debugging_tasks"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, unique=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    buggy_code = Column(Text, nullable=False)
    language = Column(String(32), nullable=False)
    expected_behavior = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)

    session = relationship("Session", back_populates="debugging_task")
    learning_states = relationship("LearningState", back_populates="task", cascade="all, delete-orphan")
    question_nodes = relationship("QuestionNode", back_populates="task", cascade="all, delete-orphan")
    proposed_fixes = relationship("ProposedFix", back_populates="task", cascade="all, delete-orphan")
    bug_hypotheses = relationship("BugHypothesis", back_populates="task", cascade="all, delete-orphan")


class LearningState(TimestampMixin, db.Model):
    """Ordered learning states (variables) within a debugging task."""
    __tablename__ = "learning_states"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("debugging_tasks.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    resolution_evidence = Column(Text, nullable=True)

    task = relationship("DebuggingTask", back_populates="learning_states")
    # Dependencies: which states must be resolved first
    depends_on = Column(JSONB, default=list)  # list of state IDs


class QuestionNode(TimestampMixin, db.Model):
    """Node in the TreeInstruct question tree."""
    __tablename__ = "question_nodes"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("debugging_tasks.id"), nullable=False, index=True)
    parent_id = Column(String(36), ForeignKey("question_nodes.id"), nullable=True)
    learning_state_id = Column(String(36), ForeignKey("learning_states.id"), nullable=True)

    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.root, nullable=False)
    depth = Column(Integer, default=0, nullable=False)
    branch_index = Column(Integer, default=0, nullable=False)
    is_answered = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    task = relationship("DebuggingTask", back_populates="question_nodes")
    children = relationship("QuestionNode", backref=db.backref("parent", remote_side=[id]))
    responses = relationship("StudentResponse", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_qnode_task_depth", "task_id", "depth"),
    )


class StudentResponse(TimestampMixin, db.Model):
    """Student's answer to a question node."""
    __tablename__ = "student_responses"

    id = Column(String(36), primary_key=True, default=_uuid)
    question_id = Column(String(36), ForeignKey("question_nodes.id"), nullable=False, index=True)
    response_text = Column(Text, nullable=False)
    verdict = Column(Enum(VerifierVerdict), nullable=True)
    verifier_justification = Column(Text, nullable=True)
    verifier_confidence = Column(Float, nullable=True)

    question = relationship("QuestionNode", back_populates="responses")


class BugHypothesis(TimestampMixin, db.Model):
    """Hypothesis about the root cause of a bug."""
    __tablename__ = "bug_hypotheses"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("debugging_tasks.id"), nullable=False, index=True)
    hypothesis_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    evidence = Column(JSONB, default=list)

    task = relationship("DebuggingTask", back_populates="bug_hypotheses")


class ProposedFix(TimestampMixin, db.Model):
    """Student-submitted fix proposal."""
    __tablename__ = "proposed_fixes"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("debugging_tasks.id"), nullable=False, index=True)
    submitted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    fixed_code = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    status = Column(Enum(FixStatus), default=FixStatus.proposed, nullable=False)
    syntax_errors = Column(JSONB, nullable=True)
    test_results = Column(JSONB, nullable=True)
    validator_notes = Column(Text, nullable=True)

    task = relationship("DebuggingTask", back_populates="proposed_fixes")


# ── LLM Audit Log ─────────────────────────────────────────────────────────────

class LLMCallLog(TimestampMixin, db.Model):
    """Audit log for every LLM API call. Enables cost and latency analysis."""
    __tablename__ = "llm_call_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=True, index=True)
    caller = Column(String(64), nullable=False)   # agent class name
    prompt_version = Column(String(64), nullable=True)
    provider = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    error_code = Column(String(64), nullable=True)
    # Do NOT store raw prompt/completion text in prod — only metadata
    request_summary = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_llm_log_session", "session_id", "created_at"),
    )


# ── Evaluation Runs ───────────────────────────────────────────────────────────

class EvaluationRun(TimestampMixin, db.Model):
    """Research evaluation experiment record."""
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    experiment_name = Column(String(128), nullable=False)
    condition = Column(String(8), nullable=False)  # A, B, C, D, E
    model_version = Column(String(64), nullable=True)
    prompt_version = Column(String(64), nullable=True)
    dataset_name = Column(String(128), nullable=True)
    sample_size = Column(Integer, nullable=True)
    config_snapshot = Column(JSONB, nullable=True)
    results = Column(JSONB, nullable=True)
    status = Column(String(32), default="pending", nullable=False)
    notes = Column(Text, nullable=True)

