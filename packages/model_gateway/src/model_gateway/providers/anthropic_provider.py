from __future__ import annotations

import os

from .base import ModelResponse, TokenUsage


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, timeout_s: int = 120, max_tokens: int = 4096):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ImportError("pip install anthropic to use AnthropicProvider") from e
            self._client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout_s)
        return self._client

    def generate(self, model: str, prompt: str, system: str | None = None) -> ModelResponse:
        client = self._get_client()

        kwargs = {
            "model": model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        resp = client.messages.create(**kwargs)

        text = ""
        for block in resp.content:
            if hasattr(block, "text"):
                text += block.text

        usage = None
        if resp.usage:
            usage = TokenUsage(
                prompt_tokens=resp.usage.input_tokens,
                completion_tokens=resp.usage.output_tokens,
            )
        return ModelResponse(
            text=text,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
            usage=usage,
        )
