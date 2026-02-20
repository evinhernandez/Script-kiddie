from __future__ import annotations

import os

from .base import ModelResponse, TokenUsage


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, timeout_s: int = 120):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.timeout_s = timeout_s
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError as e:
                raise ImportError("pip install openai to use OpenAIProvider") from e
            self._client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout_s)
        return self._client

    def generate(self, model: str, prompt: str, system: str | None = None) -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = self._get_client()
        resp = client.chat.completions.create(model=model, messages=messages)

        text = resp.choices[0].message.content or ""
        usage = None
        if resp.usage:
            usage = TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens,
                completion_tokens=resp.usage.completion_tokens,
            )
        return ModelResponse(
            text=text,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
            usage=usage,
        )
