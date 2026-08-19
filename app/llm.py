import json
import os

import httpx


class OpenRouterLLM:
    """Cliente mínimo compatível com a API OpenAI/OpenRouter."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY não configurada")

    def complete_json(self, system: str, user: str) -> dict:
        content = self._complete(system, user, json_mode=True)
        return json.loads(content)

    def complete_text(self, system: str, user: str) -> str:
        return self._complete(system, user, json_mode=False)

    def _complete(self, system: str, user: str, json_mode: bool) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
