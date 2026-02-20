from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .providers.base import ModelProvider
from .providers.ollama import OllamaProvider
from .providers.openai_compat import OpenAICompatProvider


_PROVIDER_CLASSES = {
    "ollama": OllamaProvider,
    "openai-compat": OpenAICompatProvider,
}

# Lazily registered — only loaded when actually used
_LAZY_PROVIDERS = {
    "openai": "model_gateway.providers.openai_provider:OpenAIProvider",
    "anthropic": "model_gateway.providers.anthropic_provider:AnthropicProvider",
}


def _import_class(dotted: str):
    module_path, class_name = dotted.rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _build_provider(config: dict[str, Any]) -> ModelProvider:
    provider_type = config.get("type", "ollama")

    if provider_type in _PROVIDER_CLASSES:
        cls = _PROVIDER_CLASSES[provider_type]
    elif provider_type in _LAZY_PROVIDERS:
        cls = _import_class(_LAZY_PROVIDERS[provider_type])
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    kwargs = {k: v for k, v in config.items() if k != "type"}
    return cls(**kwargs)


def load_providers(config_path: str | Path | None = None) -> dict[str, ModelProvider]:
    """Load providers from config file or environment."""
    providers: dict[str, ModelProvider] = {}

    # Try config file first
    if config_path and Path(config_path).exists():
        data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        for name, cfg in (data.get("providers") or {}).items():
            providers[name] = _build_provider(cfg)
        return providers

    # Try MODEL_PROVIDERS env var (YAML string)
    env_config = os.getenv("MODEL_PROVIDERS")
    if env_config:
        data = yaml.safe_load(env_config)
        if not isinstance(data, dict):
            raise ValueError("MODEL_PROVIDERS env var must be a YAML mapping")
        for name, cfg in data.items():
            if not isinstance(cfg, dict):
                raise ValueError(f"Provider config for '{name}' must be a mapping")
            if "type" not in cfg:
                raise ValueError(f"Provider config for '{name}' missing required 'type' field")
            providers[name] = _build_provider(cfg)
        return providers

    # Default: Ollama provider from env
    providers["ollama"] = OllamaProvider(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    return providers


def get_provider(name: str, providers: dict[str, ModelProvider] | None = None) -> ModelProvider:
    """Get a provider by name. Falls back to default Ollama if not found."""
    if providers and name in providers:
        return providers[name]
    if name == "ollama":
        return OllamaProvider()
    raise KeyError(f"Provider '{name}' not registered")
