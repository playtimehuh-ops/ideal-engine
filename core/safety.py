"""
Safety primitives for Alex.

StopController:
    A single, always-reachable "kill switch". The UI's STOP button calls
    request_stop() directly - nothing the AI does can intercept, delay,
    or disable this. Every long-running or tool-executing piece of code
    checks is_stopped() between steps and bails out early if it's set.

ConfirmationGate:
    Tools flagged as needing confirmation call ConfirmationGate.ask(), which
    blocks the calling (worker) thread until the UI shows a dialog on the
    main thread and the user answers. The AI cannot set confirm=True for
    itself or skip this - it is enforced entirely outside the AI's control,
    in core/planner.py.
"""

import threading


class StopController:
    def __init__(self):
        self._event = threading.Event()

    def request_stop(self):
        self._event.set()

    def is_stopped(self) -> bool:
        return self._event.is_set()

    def reset(self):
        """Call this once a stop has been fully handled and Alex is back at READY."""
        self._event.clear()

    @property
    def event(self) -> threading.Event:
        """Exposes the underlying Event for code that needs to wait/poll on it directly."""
        return self._event


class ConfirmationGate:
    """
    Bridges a background worker thread (which wants to run a risky tool) and
    the Qt main thread (which must own any dialog box). The UI is expected to
    set `self.show_dialog_callback` to a function that takes (tool_name, args)
    and, on the *main* thread, shows a Yes/No dialog and returns a bool.
    """

    def __init__(self):
        self.show_dialog_callback = None  # set by MainWindow at startup

    def ask(self, tool_name: str, args: dict) -> bool:
        if self.show_dialog_callback is None:
            # No UI wired up (e.g. running headless/tests) - fail safe: deny.
            return False
        return bool(self.show_dialog_callback(tool_name, args))


# Tools that must be confirmed before they run, because they act on the
# keyboard/mouse and could have unintended effects. The AI has no way to
# mark itself exempt from this list - it is enforced in core/planner.py.
CONFIRMATION_REQUIRED_TOOLS = {"click", "type_text", "press_key"}
