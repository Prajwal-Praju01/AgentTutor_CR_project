"""
TreeInstruct Instructor Agent.
Generates targeted Socratic questions for the current debugging task.
Implements child/sibling/root question generation per the paper's methodology.
"""
from __future__ import annotations

import structlog

from app.llm.adapter import LLMAdapter, LLMRequest
from app.llm.prompt_registry import PromptRegistry
from app.llm.schemas import InstructorOutput, parse_json_output
from app.models import DebuggingTask, QuestionNode, QuestionType, LearningState
from app.extensions import db

logger = structlog.get_logger()


class InstructorAgent:
    """
    Generates debugging questions using the TreeInstruct methodology:
    - Root questions: target the current unresolved learning state
    - Child questions: deepen understanding when answer is correct but incomplete
    - Sibling questions: probe a different angle when answer is incorrect
    """

    def __init__(self, llm: LLMAdapter | None = None):
        self._llm = llm or LLMAdapter()

    def generate_root_question(
        self,
        task: DebuggingTask,
        target_state: LearningState,
        prior_questions: list[str],
    ) -> QuestionNode:
        """Generate the initial (root) question for a learning state."""
        output = self._call_instructor(
            task=task,
            target_state=target_state,
            question_type="root",
            prior_questions=prior_questions,
            parent_question=None,
        )

        node = QuestionNode(
            task_id=task.id,
            parent_id=None,
            learning_state_id=target_state.id,
            question_text=output.question,
            question_type=QuestionType.root,
            depth=0,
            branch_index=0,
        )
        db.session.add(node)
        db.session.flush()
        return node

    def generate_child_question(
        self,
        task: DebuggingTask,
        parent_node: QuestionNode,
        target_state: LearningState,
        prior_questions: list[str],
    ) -> QuestionNode:
        """
        Generate a deeper question (child) when the student's answer is correct
        but understanding is not fully confirmed.
        """
        output = self._call_instructor(
            task=task,
            target_state=target_state,
            question_type="child",
            prior_questions=prior_questions,
            parent_question=parent_node.question_text,
        )

        depth = parent_node.depth + 1
        node = QuestionNode(
            task_id=task.id,
            parent_id=parent_node.id,
            learning_state_id=target_state.id,
            question_text=output.question,
            question_type=QuestionType.child,
            depth=depth,
            branch_index=0,
        )
        db.session.add(node)
        db.session.flush()
        return node

    def generate_sibling_question(
        self,
        task: DebuggingTask,
        sibling_of: QuestionNode,
        target_state: LearningState,
        prior_questions: list[str],
        sibling_index: int,
    ) -> QuestionNode:
        """
        Generate a sibling question when the student's answer is incorrect.
        Approaches the same concept from a different angle.
        """
        output = self._call_instructor(
            task=task,
            target_state=target_state,
            question_type="sibling",
            prior_questions=prior_questions,
            parent_question=sibling_of.question_text,
        )

        node = QuestionNode(
            task_id=task.id,
            parent_id=sibling_of.parent_id,
            learning_state_id=target_state.id,
            question_text=output.question,
            question_type=QuestionType.sibling,
            depth=sibling_of.depth,
            branch_index=sibling_index,
        )
        db.session.add(node)
        db.session.flush()
        return node

    def _call_instructor(
        self,
        task: DebuggingTask,
        target_state: LearningState,
        question_type: str,
        prior_questions: list[str],
        parent_question: str | None,
    ) -> InstructorOutput:
        prompt_tpl = PromptRegistry.get("instructor_system")

        prior_str = "\n".join(f"- {q}" for q in prior_questions[-10:]) if prior_questions else "None"

        context = (
            f"## Debugging Task\n{task.description}\n\n"
            f"## Buggy Code ({task.language})\n```\n{task.buggy_code[:2000]}\n```\n\n"
            f"## Target Learning State\n{target_state.name}: {target_state.description}\n\n"
            f"## Question Type Needed\n{question_type}\n\n"
            f"## Prior Questions (avoid repeating)\n{prior_str}\n"
        )
        if parent_question:
            context += f"\n## Parent/Sibling Question\n{parent_question}\n"

        req = LLMRequest(
            messages=[{"role": "user", "content": context}],
            system_prompt=prompt_tpl.system,
            temperature=0.3,
            max_tokens=512,
            caller="instructor",
            prompt_version=prompt_tpl.version,
            session_id=task.session_id,
        )
        resp = self._llm.complete(req)

        try:
            return parse_json_output(resp.content, InstructorOutput)
        except Exception as e:
            logger.warning("instructor_parse_failed", error=str(e))
            # Fallback question
            return InstructorOutput(
                question=f"What do you think is happening in the {target_state.name} part of the code?",
                question_type=question_type,
                targets_concept=target_state.name,
                reasoning="Fallback question due to parse failure",
            )

