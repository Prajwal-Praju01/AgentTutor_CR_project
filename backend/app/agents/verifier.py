"""
TreeInstruct Verifier Agent.
Classifies student responses as correct / partially_correct / incorrect / uncertain.
"""
from __future__ import annotations

import structlog

from app.llm.adapter import LLMAdapter, LLMRequest
from app.llm.prompt_registry import PromptRegistry
from app.llm.schemas import VerifierOutput, parse_json_output
from app.models import DebuggingTask, QuestionNode, StudentResponse, VerifierVerdict
from app.extensions import db

logger = structlog.get_logger()


class VerifierAgent:
    def __init__(self, llm: LLMAdapter | None = None):
        self._llm = llm or LLMAdapter()

    def verify(
        self,
        task: DebuggingTask,
        question_node: QuestionNode,
        student_response_text: str,
    ) -> tuple[VerifierOutput, StudentResponse]:
        output = self._call_verifier(task, question_node, student_response_text)
        verdict_enum = VerifierVerdict(output.verdict)

        response_record = StudentResponse(
            question_id=question_node.id,
            response_text=student_response_text,
            verdict=verdict_enum,
            verifier_justification=output.justification,
            verifier_confidence=output.confidence,
        )
        db.session.add(response_record)
        db.session.flush()

        logger.info("verifier_verdict", question_id=question_node.id, verdict=output.verdict)
        return output, response_record

    def _call_verifier(self, task: DebuggingTask, question: QuestionNode, student_response: str) -> VerifierOutput:
        prompt_tpl = PromptRegistry.get("verifier_system")
        context = (
            f"## Debugging Task\n{task.description}\n\n"
            f"## Buggy Code ({task.language})\n```\n{task.buggy_code[:2000]}\n```\n\n"
            f"## Question Asked\n{question.question_text}\n\n"
            f"## Student Response\n{student_response}\n"
        )
        req = LLMRequest(
            messages=[{"role": "user", "content": context}],
            system_prompt=prompt_tpl.system,
            temperature=0.1,
            max_tokens=512,
            caller="verifier",
            prompt_version=prompt_tpl.version,
            session_id=task.session_id,
        )
        resp = self._llm.complete(req)
        try:
            return parse_json_output(resp.content, VerifierOutput)
        except Exception as e:
            logger.warning("verifier_parse_failed", error=str(e))
            return VerifierOutput(
                verdict="uncertain",
                justification="Could not parse verifier response.",
                confidence=0.3,
            )
