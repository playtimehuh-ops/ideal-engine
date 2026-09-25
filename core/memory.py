"""
Explicit memory for Alex.

Design choice: "remember X" / "forget X" are handled deterministically with
pattern matching *before* anything is sent to the AI model. This is far more
reliable than asking a small/free language model to correctly call a
"remember" tool every time, and it matches the exact behavior described in
the spec. Recall ("what's my favorite color?") is NOT intercepted - instead,
any stored memory whose words overlap the user's current message is quietly
added to the system prompt as "known facts", and the AI answers naturally.
"""

import re
from typing import Optional

REMEMBER_PATTERN = re.compile(r"^remember\s+(that\s+)?(.+)$", re.IGNORECASE)
FORGET_PATTERN = re.compile(r"^forget\s+(that\s+)?(.+)$", re.IGNORECASE)

_STOPWORDS = {
    "the", "a", "an", "is", "my", "of", "to", "that", "what", "whats",
    "favorite", "please", "and", "in", "on", "it", "was", "were",
}


def _keywords(text: str):
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


class MemoryManager:
    def __init__(self, db):
        self.db = db

    def try_handle_command(self, user_text: str) -> Optional[str]:
        """
        If user_text is a remember/forget command, act on it and return the
        confirmation to speak back. Otherwise return None (not a memory command).
        """
        text = user_text.strip()

        m = REMEMBER_PATTERN.match(text)
        if m:
            fact = m.group(2).strip().rstrip(".")
            if not fact:
                return "I didn't catch what you wanted me to remember."
            self.db.add_memory(fact)
            self.db.log_activity("memory_remember", fact)
            return f"Got it. I'll remember that {fact}."

        m = FORGET_PATTERN.match(text)
        if m:
            target = m.group(2).strip().rstrip(".")
            keywords = _keywords(target)
            candidates = self.db.get_memories()
            matches = [
                c for c in candidates
                if keywords and keywords.issubset(_keywords(c["content"]))
            ]
            if not matches:
                # Fall back to a looser "any keyword matches" search.
                matches = [
                    c for c in candidates
                    if keywords & _keywords(c["content"])
                ]
            if not matches:
                return "I couldn't find anything matching that in my memory."
            for c in matches:
                self.db.delete_memory(c["id"])
            self.db.log_activity("memory_forget", target)
            return "Okay, I've forgotten that."

        return None

    def relevant_facts_block(self, user_text: str, max_facts: int = 5) -> str:
        """Text block for the system prompt: memories related to the current message."""
        all_memories = self.db.get_memories()
        if not all_memories:
            return "none yet"

        query_keywords = _keywords(user_text)
        if not query_keywords:
            scored = all_memories[:max_facts]
        else:
            scored = sorted(
                all_memories,
                key=lambda m: len(query_keywords & _keywords(m["content"])),
                reverse=True,
            )
            scored = [m for m in scored if query_keywords & _keywords(m["content"])][:max_facts]
            if not scored:
                return "none relevant"

        return "\n".join(f"- {m['content']}" for m in scored)
