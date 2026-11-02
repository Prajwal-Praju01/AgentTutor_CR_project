"""
Tutoring Orchestrator — Phase 3 core.
Implements the 11-step agentic tutoring loop:
Perceive → Route → Clarify → Retrieve → Plan → Instruct →
Assess → Update → Adapt → Persist → Respond
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.config import get_settings
from app.llm.adapter import LLMAdapter, LLMRequest
from app.llm.prompt_registry import PromptRegistry
from app.llm.schemas import AssessmentOutput, parse_json_output
from app.models import (
    Message, MessageRole, Session,
    StudentModel, StudentModelSnapshot, User
)
from app.extensions import db

logger = structlog.get_logger()
cfg = get_settings()


@dataclass
class OrchestratorResponse:
    content: str
    understanding_level: int = 1
    hint_depth: int = 1
    assessment: dict[str, Any] = field(default_factory=dict)
    citations: list[dict] = field(default_factory=list)
    next_question: str | None = None
    token_count: int = 0


class TutoringOrchestrator:
    """
    Manages the multi-turn tutoring loop.
    Each call processes one student message and returns a structured response.
    """

    def __init__(self, llm: LLMAdapter | None = None):
        self._llm = llm or LLMAdapter()

    def handle_message(
        self,
        session: Session,
        student_message: str,
        user: User,
    ) -> OrchestratorResponse:
        """
        Execute the full 11-step tutoring pipeline for one message.
        """
        log = logger.bind(session_id=session.id, user_id=user.id)

        # Step 1: Perceive
        history = self._load_history(session)
        student_model = self._load_student_model(user.id)
        current_level = self._get_current_level(student_model, session)
        current_depth = self._get_current_depth(student_model, session)

        # Step 2: Route
        concept = session.concept or "general"
        course_id = session.course_id

        # Step 3: Clarify (simple heuristic — LLM will handle in response)
        # If message is very short and first message, note it but continue
        needs_clarification = len(student_message.strip()) < 10 and not history

        # Step 4: Retrieve relevant course materials
        citations: list[dict] = []
        retrieved_context = ""
        if course_id and not needs_clarification:
            citations, retrieved_context = self._retrieve(course_id, student_message)

        # Step 5: Plan — select hint depth based on student model
        planned_depth = self._plan_hint_depth(
            current_level, current_depth, student_message
        )

        # Check for "give up" condition
        if self._is_give_up_request(student_message):
            planned_depth = 4  # Full solution

        # Step 6: Instruct — generate Socratic response
        response_content, token_count = self._instruct(
            session=session,
            history=history,
            student_message=student_message,
            retrieved_context=retrieved_context,
            hint_depth=planned_depth,
            understanding_level=current_level,
        )

        # Step 7: Assess — evaluate student's demonstrated understanding
        assessment = self._assess(
            student_message=student_message,
            history=history,
            concept=concept,
        )

        new_level = assessment.understanding_level
        new_depth = assessment.recommended_hint_depth

        # Step 8 & 9: Update student model
        self._update_student_model(
            student_model=student_model,
            session=session,
            assessment=assessment,
            concept=concept,
        )

        # Step 10: Persist snapshot (done in caller after both messages are saved)
        # We return the data; caller persists.

        # Step 11: Compose response
        next_question = self._extract_next_question(response_content)

        log.info(
            "tutoring_response_generated",
            understanding_level=new_level,
            hint_depth=new_depth,
            citations=len(citations),
        )

        return OrchestratorResponse(
            content=response_content,
            understanding_level=new_level,
            hint_depth=new_depth,
            assessment=assessment.model_dump(),
            citations=citations,
            next_question=next_question,
            token_count=token_count,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_history(self, session: Session) -> list[dict[str, str]]:
        messages = (
            Message.query
            .filter_by(session_id=session.id)
            .order_by(Message.created_at)
            .limit(20)  # Bounded context window
            .all()
        )
        return [
            {"role": "user" if m.role == MessageRole.student else "assistant", "content": m.content}
            for m in messages
        ]

    def _load_student_model(self, user_id: str) -> StudentModel | None:
        return StudentModel.query.filter_by(user_id=user_id).first()

    def _get_current_level(self, student_model: StudentModel | None, session: Session) -> int:
        if not student_model:
            return 1
        # Get last snapshot for this session
        last_snap = (
            StudentModelSnapshot.query
            .filter_by(session_id=session.id)
            .order_by(StudentModelSnapshot.created_at.desc())
            .first()
        )
        return last_snap.understanding_level if last_snap else 1

    def _get_current_depth(self, student_model: StudentModel | None, session: Session) -> int:
        if not student_model:
            return 1
        last_snap = (
            StudentModelSnapshot.query
            .filter_by(session_id=session.id)
            .order_by(StudentModelSnapshot.created_at.desc())
            .first()
        )
        return last_snap.hint_depth if last_snap else 1

    def _retrieve(self, course_id: str, query: str) -> tuple[list[dict], str]:
        """Retrieve relevant course materials. Returns (citations, context_text)."""
        try:
            from app.retrieval.retriever import Retriever
            retriever = Retriever()
            results = retriever.search(course_id=course_id, query=query, top_k=cfg.retrieval_top_k)
            context = "\n\n---\n\n".join(r["content"] for r in results)
            citations = [
                {
                    "document": r.get("document_name", "Unknown"),
                    "section": r.get("section_title"),
                    "page": r.get("page_number"),
                    "relevance": r.get("score", 0.0),
                }
                for r in results
            ]
            return citations, context
        except Exception as e:
            logger.warning("retrieval_failed", error=str(e))
            return [], ""

    def _plan_hint_depth(self, current_level: int, current_depth: int, message: str) -> int:
        """
        Adaptive hint depth policy.
        Level 0 → start at depth 2; level 3 → stay at depth 1.
        Progressive escalation within a session.
        """
        from app.tutoring.adaptive_policy import AdaptivePolicy
        return AdaptivePolicy.select_hint_depth(current_level, current_depth, message)

    def _is_give_up_request(self, message: str) -> bool:
        triggers = ["give up", "show me the solution", "just tell me", "i don't know, explain"]
        return any(t in message.lower() for t in triggers)

    def _instruct(
        self,
        session: Session,
        history: list[dict[str, str]],
        student_message: str,
        retrieved_context: str,
        hint_depth: int,
        understanding_level: int,
    ) -> tuple[str, int]:
        """Generate the Socratic tutor response."""
        prompt_tpl = PromptRegistry.get("tutor_system")

        # Inject retrieved context into system prompt if available
        system = prompt_tpl.system
        if retrieved_context:
            system += (
                "\n\n## Retrieved Course Materials\n"
                "Use the following excerpts to ground your response. "
                "Cite them as [Source: ...] when referenced.\n\n"
                + retrieved_context[:3000]  # Bounded context injection
            )
        system += f"\n\n## Current Session State\n- Understanding level: {understanding_level}/3\n- Hint depth: {hint_depth}/4"

        messages = list(history) + [{"role": "user", "content": student_message}]

        req = LLMRequest(
            messages=messages,
            system_prompt=system,
            caller="tutor_orchestrator",
            prompt_version=prompt_tpl.version,
            session_id=session.id,
        )
        resp = self._llm.complete(req)
        return resp.content, resp.prompt_tokens + resp.completion_tokens

    def _assess(
        self,
        student_message: str,
        history: list[dict[str, str]],
        concept: str,
    ) -> AssessmentOutput:
        """Assess the student's understanding from their message."""
        prompt_tpl = PromptRegistry.get("assessment_system")

        # Build assessment context
        context = f"Concept being studied: {concept}\n\nStudent's message:\n{student_message}"
        if history:
            last_exchange = history[-2:] if len(history) >= 2 else history
            context += "\n\nRecent exchange:\n" + "\n".join(
                f"{m['role'].upper()}: {m['content'][:500]}" for m in last_exchange
            )

        req = LLMRequest(
            messages=[{"role": "user", "content": context}],
            system_prompt=prompt_tpl.system,
            temperature=0.1,
            max_tokens=512,
            caller="state_estimator",
            prompt_version=prompt_tpl.version,
        )
        resp = self._llm.complete(req)

        try:
            return parse_json_output(resp.content, AssessmentOutput)
        except Exception as e:
            logger.warning("assessment_parse_failed", error=str(e), raw=resp.content[:200])
            # Fallback: return a safe default
            return AssessmentOutput(
                understanding_level=1,
                justification="Assessment could not be parsed; defaulting to beginner level.",
                confidence=0.5,
                misconceptions=[],
                recommended_hint_depth=2,
            )

    def _update_student_model(
        self,
        student_model: StudentModel | None,
        session: Session,
        assessment: AssessmentOutput,
        concept: str,
    ) -> None:
        if not student_model:
            return

        # Update concept scores (running average)
        scores = dict(student_model.concept_scores or {})
        current_score = scores.get(concept, 1.0)
        scores[concept] = round(0.7 * current_score + 0.3 * assessment.understanding_level, 2)
        student_model.concept_scores = scores

        # Update misconceptions list (bounded to 50 entries)
        misconceptions = list(student_model.misconceptions or [])
        for m in assessment.misconceptions:
            existing = next((x for x in misconceptions if x.get("description") == m), None)
            if existing:
                existing["count"] = existing.get("count", 1) + 1
            else:
                misconceptions.append({"concept": concept, "description": m, "count": 1})
        student_model.misconceptions = misconceptions[-50:]

        student_model.total_messages = (student_model.total_messages or 0) + 1

        db.session.add(student_model)

        # Create snapshot
        snapshot = StudentModelSnapshot(
            student_model_id=student_model.id,
            session_id=session.id,
            understanding_level=assessment.understanding_level,
            hint_depth=assessment.recommended_hint_depth,
            concept=concept,
            justification=assessment.justification,
            confidence=assessment.confidence,
            identified_misconceptions=assessment.misconceptions,
        )
        db.session.add(snapshot)

    def _extract_next_question(self, content: str) -> str | None:
        """Extract the last question from the tutor's response, if any."""
        lines = content.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line.endswith("?") and len(line) > 20:
                return line
        return None
