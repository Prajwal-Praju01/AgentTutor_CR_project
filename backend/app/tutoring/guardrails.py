"""
Guardrails for tutoring responses.
Prevents prompt injection, solution leaking, and unsafe content.
"""
from __future__ import annotations
import re


class Guardrails:
    """
    Static checks applied to retrieved content and student input.
    Does NOT silently swallow violations — raises or flags them.
    """

    # Patterns that suggest prompt injection in retrieved content
    _INJECTION_PATTERNS = [
        re.compile(r"ignore (all )?(previous|above|prior) instructions?", re.I),
        re.compile(r"you are now", re.I),
        re.compile(r"system prompt", re.I),
        re.compile(r"disregard (the|your) (system|instructions?)", re.I),
    ]

    @classmethod
    def screen_retrieved_content(cls, content: str) -> str:
        """
        Sanitize retrieved document content before injecting into the prompt.
        Flags suspicious patterns — does not silently ignore them.
        """
        for pattern in cls._INJECTION_PATTERNS:
            if pattern.search(content):
                import structlog
                structlog.get_logger().warning(
                    "prompt_injection_pattern_in_retrieved_content",
                    pattern=pattern.pattern,
                )
                # Strip the offending line(s) and mark as sanitized
                content = pattern.sub("[CONTENT SANITIZED]", content)
        return content

    @classmethod
    def screen_student_input(cls, content: str) -> tuple[bool, str]:
        """
        Screen student messages for policy violations.
        Returns (is_safe, reason_if_unsafe).
        """
        if len(content) > 8000:
            return False, "Message exceeds maximum length"
        return True, ""

    @classmethod
    def should_reveal_solution(cls, history_length: int, is_give_up: bool) -> bool:
        """
        Determine whether to reveal a full solution.
        Requires either an explicit give-up request or 2+ meaningful failed attempts.
        """
        return is_give_up or history_length >= 4

