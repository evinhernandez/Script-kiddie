from __future__ import annotations
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "")
API_KEY = os.getenv("API_KEY", "dev-local-key")
POLICY_PATH = os.getenv("POLICY_PATH", "policies/default.yml")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL_ANALYZER = os.getenv("OLLAMA_MODEL_ANALYZER", "llama3.1")
OLLAMA_MODEL_JUDGE = os.getenv("OLLAMA_MODEL_JUDGE", "llama3.1")
