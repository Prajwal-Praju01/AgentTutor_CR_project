"""
Provider-independent LLM adapter.
Supports: openai | anthropic | google | mock
All providers implement the same interface so the rest of the application
never imports a vendor SDK directly.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()
cfg = get_settings()


@dataclass
class LLMRequest:
    messages: list[dict[str, str]]
    system_prompt: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048
    caller: str = "unknown"
    prompt_version: str = "unversioned"
    session_id: str | None = None


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    model: str = ""
    raw: Any = None


class LLMError(Exception):
    """Raised when the LLM call fails after retries."""


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, req: LLMRequest) -> LLMResponse: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...


# ── Mock Provider (deterministic, no API key) ─────────────────────────────────

class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock for tests and local development without an API key."""

    _model_name = "mock-tutor-v1"

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete(self, req: LLMRequest) -> LLMResponse:
        last_user_msg = next(
            (m["content"] for m in reversed(req.messages) if m["role"] == "user"),
            "",
        )
        content = self._generate_mock_response(last_user_msg, req.caller)
        return LLMResponse(
            content=content,
            prompt_tokens=len(" ".join(m["content"] for m in req.messages).split()),
            completion_tokens=len(content.split()),
            latency_ms=50,
            model=self._model_name,
        )

    def _generate_mock_response(self, user_message: str, caller: str) -> str:
        msg_lower = user_message.lower()

        if caller == "verifier":
            return '{"verdict": "partially_correct", "justification": "The student shows some understanding but has not identified the root cause.", "confidence": 0.6}'

        if caller == "state_estimator":
            return '{"understanding_level": 1, "justification": "The student is at beginner level for this concept.", "confidence": 0.7, "misconceptions": []}'

        if "give up" in msg_lower or "show me the solution" in msg_lower:
            return (
                "Let me walk you through the complete solution step by step.\n\n"
                "**Solution:**\n"
                "Here is the corrected approach, explained at each stage so you can follow the reasoning:\n"
                "1. First, identify the core issue...\n"
                "2. Then apply the fix...\n"
                "3. Finally, verify the result..."
            )

        if "hint" in msg_lower or "help" in msg_lower:
            return (
                "Great question! Let me give you a conceptual hint to guide your thinking.\n\n"
                "**Hint:** Think about what the function is supposed to return. "
                "What does the current code return instead?\n\n"
                "What do you think might be causing the discrepancy?"
            )

        return (
            "That's an interesting observation! Let me help you think through this.\n\n"
            "**Socratic Question:** Before I explain, can you tell me what you think "
            "the expected output should be when you run this code?\n\n"
            "Understanding your current mental model will help me guide you more effectively."
        )


# ── OpenAI Provider ────────────────────────────────────────────────────────────

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=cfg.llm_api_key, timeout=cfg.llm_timeout_seconds)
        except ImportError:
            raise LLMError("openai package not installed")

    @property
    def model_name(self) -> str:
        return cfg.llm_model

    def complete(self, req: LLMRequest) -> LLMResponse:
        messages = []
        if req.system_prompt:
            messages.append({"role": "system", "content": req.system_prompt})
        messages.extend(req.messages)

        start = time.time()
        resp = self._client.chat.completions.create(
            model=cfg.llm_model,
            messages=messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        latency_ms = int((time.time() - start) * 1000)

        return LLMResponse(
            content=resp.choices[0].message.content or "",
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            latency_ms=latency_ms,
            model=cfg.llm_model,
            raw=resp,
        )


# ── Anthropic Provider ─────────────────────────────────────────────────────────

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=cfg.llm_api_key)
        except ImportError:
            raise LLMError("anthropic package not installed")

    @property
    def model_name(self) -> str:
        return cfg.llm_model

    def complete(self, req: LLMRequest) -> LLMResponse:
        start = time.time()
        resp = self._client.messages.create(
            model=cfg.llm_model,
            system=req.system_prompt,
            messages=req.messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        latency_ms = int((time.time() - start) * 1000)

        return LLMResponse(
            content=resp.content[0].text,
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
            latency_ms=latency_ms,
            model=cfg.llm_model,
            raw=resp,
        )


# ── LLM Adapter (public interface) ────────────────────────────────────────────

class LLMAdapter:
    """
    Unified interface. Selects the provider from config, adds retry logic,
    and writes to the audit log.
    """

    def __init__(self, provider: BaseLLMProvider | None = None):
        self._provider = provider or _build_provider()

    def complete(self, req: LLMRequest) -> LLMResponse:
        last_err: Exception | None = None
        for attempt in range(1, cfg.llm_max_retries + 1):
            try:
                resp = self._provider.complete(req)
                self._log(req, resp, success=True)
                return resp
            except Exception as e:
                last_err = e
                logger.warning("llm_retry", attempt=attempt, error=str(e), caller=req.caller)
                time.sleep(0.5 * attempt)  # simple back-off

        self._log(req, None, success=False, error=str(last_err))
        raise LLMError(f"LLM call failed after {cfg.llm_max_retries} attempts: {last_err}") from last_err

    def _log(self, req: LLMRequest, resp: LLMResponse | None, success: bool, error: str | None = None) -> None:
        try:
            from app.extensions import db
            from app.models import LLMCallLog
            log = LLMCallLog(
                session_id=req.session_id,
                caller=req.caller,
                prompt_version=req.prompt_version,
                provider=cfg.llm_provider,
                model=self._provider.model_name,
                prompt_tokens=resp.prompt_tokens if resp else None,
                completion_tokens=resp.completion_tokens if resp else None,
                latency_ms=resp.latency_ms if resp else None,
                success=success,
                error_code=error[:64] if error else None,
                request_summary=f"caller={req.caller} msgs={len(req.messages)}",
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            pass  # Never crash the main flow due to logging failure


def _build_provider() -> BaseLLMProvider:
    provider_map = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mock": MockLLMProvider,
    }
    cls = provider_map.get(cfg.llm_provider)
    if cls is None:
        logger.warning("unknown_llm_provider", provider=cfg.llm_provider, fallback="mock")
        return MockLLMProvider()
    return cls()
