from __future__ import annotations

# Pricing per 1M tokens (USD)
# Updated periodically — values are approximations for cost tracking
PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
    # Anthropic
    "claude-sonnet-4-6": {"prompt": 3.00, "completion": 15.00},
    "claude-haiku-4-5-20251001": {"prompt": 0.80, "completion": 4.00},
    "claude-opus-4-6": {"prompt": 15.00, "completion": 75.00},
    # Ollama / local — effectively free
    "llama3.1": {"prompt": 0.0, "completion": 0.0},
    "llama3.2": {"prompt": 0.0, "completion": 0.0},
    "mistral": {"prompt": 0.0, "completion": 0.0},
    "qwen2.5": {"prompt": 0.0, "completion": 0.0},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD for a model call."""
    pricing = PRICING.get(model)
    if not pricing:
        return 0.0
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)
