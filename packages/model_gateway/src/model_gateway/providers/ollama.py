from __future__ import annotations

import os

import requests

from .base import ModelResponse, TokenUsage


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str | None = None, timeout_s: int = 180):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout_s = timeout_s

    def generate(self, model: str, prompt: str, system: str | None = None) -> ModelResponse:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        usage = None
        if "prompt_eval_count" in data or "eval_count" in data:
            usage = TokenUsage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
            )
        return ModelResponse(text=data.get("response", ""), raw=data, usage=usage)
