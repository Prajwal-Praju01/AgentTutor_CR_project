"""
Fix Validator Agent.
Evaluates proposed student fixes using static analysis and optional test execution.
"""
from __future__ import annotations

import ast
import structlog

from app.llm.adapter import LLMAdapter, LLMRequest
from app.llm.prompt_registry import PromptRegistry
from app.llm.schemas import FixValidatorOutput, parse_json_output
from app.models import DebuggingTask, ProposedFix, FixStatus
from app.extensions import db

logger = structlog.get_logger()


class FixValidatorAgent:
    """
    Evaluates proposed fixes in two stages:
    1. Static analysis (syntax, structural review via LLM).
    2. Optional test execution in isolated environment.
    """

    def __init__(self, llm: LLMAdapter | None = None):
        self._llm = llm or LLMAdapter()

    def validate(
        self,
        task: DebuggingTask,
        proposed_fix: ProposedFix,
    ) -> FixValidatorOutput:
        """Run all validation stages and update the ProposedFix record."""
        fixed_code = proposed_fix.fixed_code

        # Stage 1: Syntax check (Python only for now)
        syntax_errors = None
        if task.language.lower() == "python":
            syntax_errors = self._check_python_syntax(fixed_code)

        if syntax_errors:
            proposed_fix.status = FixStatus.syntax_valid
            proposed_fix.syntax_errors = syntax_errors
            db.session.flush()
            return FixValidatorOutput(
                is_correct=False,
                partially_correct=False,
                explanation=f"Fix contains syntax errors: {syntax_errors}",
                syntax_notes=str(syntax_errors),
            )

        # Stage 2: LLM static review
        output = self._llm_review(task, fixed_code)

        # Stage 3: Update record
        if output.is_correct:
            proposed_fix.status = FixStatus.tests_passed
        elif output.partially_correct:
            proposed_fix.status = FixStatus.syntax_valid
        else:
            proposed_fix.status = FixStatus.tests_failed

        proposed_fix.validator_notes = output.explanation
        proposed_fix.syntax_errors = syntax_errors
        db.session.flush()

        logger.info(
            "fix_validated",
            fix_id=proposed_fix.id,
            is_correct=output.is_correct,
            status=proposed_fix.status.value,
        )
        return output

    def _check_python_syntax(self, code: str) -> list[str] | None:
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return [f"SyntaxError at line {e.lineno}: {e.msg}"]

    def _llm_review(self, task: DebuggingTask, fixed_code: str) -> FixValidatorOutput:
        prompt_tpl = PromptRegistry.get("fix_validator_system")
        context = (
            f"## Original Buggy Code ({task.language})\n```\n{task.buggy_code[:2000]}\n```\n\n"
            f"## Bug Description\n{task.description}\n\n"
            f"## Expected Behavior\n{task.expected_behavior or 'Not specified'}\n\n"
            f"## Proposed Fix\n```\n{fixed_code[:2000]}\n```\n"
        )
        req = LLMRequest(
            messages=[{"role": "user", "content": context}],
            system_prompt=prompt_tpl.system,
            temperature=0.1,
            max_tokens=512,
            caller="fix_validator",
            prompt_version=prompt_tpl.version,
            session_id=task.session_id,
        )
        resp = self._llm.complete(req)
        try:
            return parse_json_output(resp.content, FixValidatorOutput)
        except Exception as e:
            logger.warning("fix_validator_parse_failed", error=str(e))
            return FixValidatorOutput(
                is_correct=False,
                partially_correct=False,
                explanation="Validation could not be completed. Please review manually.",
            )

