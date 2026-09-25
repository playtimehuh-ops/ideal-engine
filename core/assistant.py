"""
Assistant - the pipeline behind every request, voice or typed:

  1. Is this a "remember X" / "forget X" command? Handle it directly.
  2. Otherwise, ask the AI, with recent history + relevant memories as context.
  3. If the AI's reply is a tool-call JSON, run it (through confirmation +
     stop checks) and ask the AI once more for a natural reply describing
     what happened.
  4. Return the final text for the UI to show and TTS to speak.

This class does no I/O with Qt directly - it's called from a worker thread,
and reports progress through plain callback functions so the UI stays
responsive and any widget updates happen through Qt's own thread-safe signals
in ui/main_window.py.
"""

from core.planner import build_system_prompt, parse_action, run_tool

HISTORY_TURNS = 10


class Assistant:
    def __init__(self, db, memory, get_ai_provider, confirmation_gate, stop_controller,
                 on_state=None, on_error=None):
        self.db = db
        self.memory = memory
        self.get_ai_provider = get_ai_provider  # callable -> BaseAIProvider (may raise/None if no key)
        self.confirmation_gate = confirmation_gate
        self.stop_controller = stop_controller
        self.on_state = on_state or (lambda state, detail="": None)
        self.on_error = on_error or (lambda msg: None)

    def _history_messages(self):
        return [{"role": m["role"], "content": m["content"]} for m in self.db.get_recent_messages(HISTORY_TURNS)]

    def handle_utterance(self, user_text: str, temperature: float = 0.7) -> str:
        user_text = (user_text or "").strip()
        if not user_text:
            return ""

        self.db.add_message("user", user_text)
        self.db.log_activity("user_utterance", user_text)

        # 1) Deterministic memory commands bypass the AI entirely - more
        #    reliable than trusting a small/free model to call a tool for it.
        memory_reply = self.memory.try_handle_command(user_text)
        if memory_reply is not None:
            self.db.add_message("assistant", memory_reply)
            return memory_reply

        provider = self.get_ai_provider()
        if provider is None:
            msg = "No OpenRouter API key is set yet. Add one in Settings and I'll be ready to go."
            self.on_error(msg)
            return msg

        self.on_state("THINKING")
        memory_block = self.memory.relevant_facts_block(user_text)
        system_prompt = build_system_prompt(memory_block)
        messages = [{"role": "system", "content": system_prompt}] + self._history_messages()
        messages.append({"role": "user", "content": user_text})

        response = provider.chat(messages, temperature=temperature)
        if response.error:
            self.on_error(response.error)
            return response.error

        if self.stop_controller.is_stopped():
            return "Cancelled."

        tool_name, args = parse_action(response.text)
        if tool_name is None:
            final_text = response.text.strip() or "I'm not sure how to answer that."
            self.db.add_message("assistant", final_text)
            return final_text

        # It's a tool call.
        state = "SEARCHING" if tool_name == "web_search" else "ACTION"
        self.on_state(state, tool_name)

        tool_result = run_tool(tool_name, args, self.confirmation_gate, self.stop_controller, self.db)

        if self.stop_controller.is_stopped():
            return "Cancelled."

        self.on_state("THINKING")
        followup_messages = messages + [
            {"role": "assistant", "content": response.text},
            {"role": "user", "content": f"[Tool result: {tool_result}] "
                                          f"Now reply to the user naturally in one short sentence, "
                                          f"describing the outcome. Do not output JSON this time."},
        ]
        followup = provider.chat(followup_messages, temperature=temperature)
        final_text = followup.text.strip() if not followup.error else tool_result

        self.db.add_message("assistant", final_text)
        return final_text
