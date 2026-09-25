"""
OpenRouter provider for Alex.

Uses the standard OpenRouter chat-completions endpoint (OpenAI-compatible).
No API key ever appears in source code - it's passed in at construction time,
read by the caller from config.settings.get_api_key().

Note on tool/function calling: many free-tier OpenRouter models do not reliably
support native "tools" function-calling. To keep Alex working across whichever
free model the user picks, Alex does NOT depend on native tool calling - see
core/planner.py, which uses a plain-text JSON convention instead. This client
is therefore a deliberately simple chat() call.
"""

import requests
from typing import List, Dict

from ai.base import BaseAIProvider, AIResponse

API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30


class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> AIResponse:
        if not self.api_key:
            return AIResponse(error="No OpenRouter API key is set. Add one in Settings.", error_kind="auth")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter asks integrations to identify themselves - harmless, no user data.
            "HTTP-Referer": "https://alex.local/",
            "X-Title": "Alex Desktop Assistant",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.exceptions.Timeout:
            return AIResponse(error="The AI provider took too long to respond.", error_kind="network")
        except requests.exceptions.ConnectionError:
            return AIResponse(error="I'm offline right now, so I can't reach my AI provider.", error_kind="network")
        except requests.exceptions.RequestException as e:
            return AIResponse(error=f"Network error talking to OpenRouter: {e}", error_kind="network")

        if resp.status_code == 401:
            return AIResponse(error="That OpenRouter API key was rejected. Check it in Settings.", error_kind="auth")
        if resp.status_code == 429:
            return AIResponse(
                error="OpenRouter is rate-limiting this model right now. Try again shortly, "
                      "or switch models in Settings.",
                error_kind="rate_limit",
            )
        if resp.status_code >= 500:
            return AIResponse(error="OpenRouter is having server trouble right now.", error_kind="server")
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                pass
            return AIResponse(error=f"OpenRouter rejected the request. {detail}".strip(), error_kind="other")

        try:
            data = resp.json()
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
            return AIResponse(text=content.strip())
        except (KeyError, IndexError, ValueError):
            return AIResponse(error="Got an unexpected response shape from OpenRouter.", error_kind="other")
