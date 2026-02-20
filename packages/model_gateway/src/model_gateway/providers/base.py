from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ModelResponse(BaseModel):
    text: str
    raw: dict | None = None
    usage: TokenUsage | None = None


@runtime_checkable
class ModelProvider(Protocol):
    name: str

    def generate(self, model: str, prompt: str, system: str | None = None) -> ModelResponse: ...
