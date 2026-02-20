from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from model_gateway.providers.ollama import ModelResponse, OllamaProvider


class TestOllamaProvider:
    def test_defaults(self):
        p = OllamaProvider()
        assert "11434" in p.base_url
        assert p.name == "ollama"

    def test_custom_base_url(self):
        p = OllamaProvider(base_url="http://custom:1234")
        assert p.base_url == "http://custom:1234"

    @patch("model_gateway.providers.ollama.requests.post")
    def test_generate_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Hello world"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        provider = OllamaProvider(base_url="http://test:11434")
        result = provider.generate("llama3.1", prompt="Hi", system="Be helpful")

        assert isinstance(result, ModelResponse)
        assert result.text == "Hello world"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["model"] == "llama3.1"
        assert payload["prompt"] == "Hi"
        assert payload["system"] == "Be helpful"

    @patch("model_gateway.providers.ollama.requests.post")
    def test_generate_without_system(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "Ok"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        provider = OllamaProvider(base_url="http://test:11434")
        result = provider.generate("llama3.1", prompt="Hi")

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert "system" not in payload

    @patch("model_gateway.providers.ollama.requests.post")
    def test_generate_empty_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        provider = OllamaProvider(base_url="http://test:11434")
        result = provider.generate("llama3.1", prompt="Hi")
        assert result.text == ""

    @patch("model_gateway.providers.ollama.requests.post")
    def test_generate_http_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.HTTPError("500 Server Error")
        provider = OllamaProvider(base_url="http://test:11434")
        with pytest.raises(requests.HTTPError):
            provider.generate("llama3.1", prompt="Hi")
