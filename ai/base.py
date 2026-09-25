"""
Base interface for AI providers.

To add a new provider later (e.g. a different API), subclass BaseAIProvider
and implement chat(). Nothing else in the app needs to change - core/assistant.py
only ever talks to this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class AIResponse:
    text: str = ""
    error: Optional[str] = None          # human-readable error, or None on success
    error_kind: Optional[str] = None      # "auth" | "rate_limit" | "network" | "server" | "other"


class BaseAIProvider(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> AIResponse:
        """
        messages: list of {"role": "system"|"user"|"assistant", "content": str}
        Returns an AIResponse. Never raises - all failures come back as AIResponse.error.
        """
        raise NotImplementedError
