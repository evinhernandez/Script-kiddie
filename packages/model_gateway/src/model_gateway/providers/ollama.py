from __future__ import annotations
import os
import requests
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ModelResponse(BaseModel):
    text: str
    raw: Optional[Dict[str, Any]] = None

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
        return ModelResponse(text=data.get("response", ""), raw=data)
