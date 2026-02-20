from __future__ import annotations

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

REDIS_URL = os.environ.get("REDIS_URL", "")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is required")

API_KEY = os.environ.get("API_KEY", "")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required — set a strong random value")

POLICY_PATH = os.getenv("POLICY_PATH", "policies/default.yml")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL_ANALYZER = os.getenv("OLLAMA_MODEL_ANALYZER", "llama3.1")
OLLAMA_MODEL_JUDGE = os.getenv("OLLAMA_MODEL_JUDGE", "llama3.1")

CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
).split(",") if o.strip()]
