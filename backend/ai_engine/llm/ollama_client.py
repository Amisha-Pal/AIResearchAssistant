"""Minimal HTTP client for a local Ollama server (https://github.com/ollama/ollama/blob/main/docs/api.md)."""

import requests


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


class OllamaClient:
    def __init__(self, base_url, timeout=120.0, session=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _get(self, path):
        try:
            response = self.session.get(f"{self.base_url}{path}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise OllamaError(f"Ollama request to {path} failed: {exc}") from exc
        except ValueError as exc:
            raise OllamaError(f"Ollama returned invalid JSON for {path}.") from exc

    def version(self):
        return self._get("/api/version").get("version", "unknown")

    def list_models(self):
        return [m["name"] for m in self._get("/api/tags").get("models", []) if "name" in m]

    def status(self):
        return {"version": self.version(), "models": self.list_models()}
