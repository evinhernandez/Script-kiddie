from __future__ import annotations
import os

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+psycopg://scriptkiddie:scriptkiddie@postgres:5432/scriptkiddie"
REDIS_URL = os.getenv("REDIS_URL") or "redis://redis:6379/0"
API_KEY = os.getenv("API_KEY", "dev-local-key")
POLICY_PATH = os.getenv("POLICY_PATH", "policies/default.yml")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL_ANALYZER = os.getenv("OLLAMA_MODEL_ANALYZER", "llama3.1")
OLLAMA_MODEL_JUDGE = os.getenv("OLLAMA_MODEL_JUDGE", "llama3.1")

CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",") if o.strip()]
