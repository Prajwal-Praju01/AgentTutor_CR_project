"""
Stopping controller for the TreeInstruct debugging loop.
Decides when to stop questioning and mark a task as resolved or unresolved.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class StoppingDecision:
    should_stop: bool
    reason: str
    mark_resolved: bool = False


class StoppingController:
    """
    Implements evidence-based stopping conditions for TreeInstruct.
    Configuration is read from settings to keep it adjustable without code changes.
    """

    MAX_DEPTH = 5
    MAX_SIBLINGS = 3
    MAX_TOTAL_QUESTIONS = 20
    MIN_CORRECT_TO_RESOLVE = 2

    @classmethod
    def evaluate(
        cls,
        depth: int,
        sibling_count: int,
        total_questions: int,
        correct_count: int,
        consecutive_incorrect: int,
        is_fix_validated: bool,
    ) -> StoppingDecision:
        # Verified fix → resolved
        if is_fix_validated:
            return StoppingDecision(
                should_stop=True,
                reason="Fix validated successfully",
                mark_resolved=True,
            )

        # Sufficient correct answers → resolved
        if correct_count >= cls.MIN_CORRECT_TO_RESOLVE:
            return StoppingDecision(
                should_stop=True,
                reason=f"Student demonstrated understanding ({correct_count} correct responses)",
                mark_resolved=True,
            )

        # Hard depth limit
        if depth >= cls.MAX_DEPTH:
            return StoppingDecision(
                should_stop=True,
                reason=f"Maximum question depth ({cls.MAX_DEPTH}) reached",
                mark_resolved=False,
            )

        # Sibling exhaustion
        if sibling_count >= cls.MAX_SIBLINGS:
            return StoppingDecision(
                should_stop=True,
                reason=f"Maximum sibling questions ({cls.MAX_SIBLINGS}) exhausted at this level",
                mark_resolved=False,
            )

        # Total question limit
        if total_questions >= cls.MAX_TOTAL_QUESTIONS:
            return StoppingDecision(
                should_stop=True,
                reason=f"Maximum total questions ({cls.MAX_TOTAL_QUESTIONS}) reached",
                mark_resolved=False,
            )

        # Persistent failure (consecutive incorrect) → teaching fallback
        if consecutive_incorrect >= 3:
            return StoppingDecision(
                should_stop=True,
                reason="Student has given 3 consecutive incorrect responses; switching to teaching mode",
                mark_resolved=False,
            )

        return StoppingDecision(should_stop=False, reason="Continue")

