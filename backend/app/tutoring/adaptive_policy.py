"""
Adaptive hint depth policy.
Implements evidence-based hint escalation based on student understanding level,
current depth, and message patterns.
"""
from __future__ import annotations


class AdaptivePolicy:
    """
    Stateless policy for selecting hint depth.
    The depth escalates when the student is struggling and de-escalates
    when they demonstrate understanding.
    """

    # Mapping: (understanding_level) -> base hint depth
    _BASE_DEPTH = {3: 1, 2: 1, 1: 2, 0: 2}

    # Maximum depth escalation per turn
    _MAX_ESCALATION = 1

    @classmethod
    def select_hint_depth(
        cls,
        understanding_level: int,
        current_depth: int,
        student_message: str,
    ) -> int:
        """Select the appropriate hint depth for the next response."""
        base = cls._BASE_DEPTH.get(understanding_level, 2)

        # Escalate if confusion signals present
        if cls._is_confused(student_message):
            new_depth = min(current_depth + cls._MAX_ESCALATION, 4)
        elif understanding_level >= 2:
            # De-escalate when doing well
            new_depth = max(base, 1)
        else:
            # Stay at current or move to base, whichever is higher
            new_depth = max(current_depth, base)

        return max(1, min(4, new_depth))

    @classmethod
    def _is_confused(cls, message: str) -> bool:
        """Detect confusion signals in student messages."""
        confusion_signals = [
            "don't understand",
            "confused",
            "not sure",
            "lost",
            "no idea",
            "what do you mean",
            "can you explain",
            "i'm stuck",
            "stuck",
        ]
        msg_lower = message.lower()
        return any(signal in msg_lower for signal in confusion_signals)

