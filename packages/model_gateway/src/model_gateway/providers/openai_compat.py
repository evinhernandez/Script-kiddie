from __future__ import annotations

import os

import requests

from .base import ModelResponse, TokenUsage


class OpenAICompatProvider:
    """Provider for any OpenAI-compatible API (vLLM, LM Studio, etc.)."""

    name = "openai-compat"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_s: int = 180,
        provider_name: str | None = None,
    ):
        self.base_url = (base_url or os.getenv("OPENAI_COMPAT_BASE_URL", "http://localhost:8080")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_COMPAT_API_KEY", "")
        self.timeout_s = timeout_s
        if provider_name:
            self.name = provider_name

    def generate(self, model: str, prompt: str, system: str | None = None) -> ModelResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"model": model, "messages": messages}
        r = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()

        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = None
        usage_data = data.get("usage")
        if usage_data:
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
            )
        return ModelResponse(text=text, raw=data, usage=usage)
