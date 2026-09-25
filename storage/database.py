"""
Local SQLite storage for Alex.

Everything here stays on the user's machine (config.settings.data_dir()).
Three tables:
  - memories: facts the user explicitly asked Alex to remember
  - conversation: rolling chat history, used for short-term context
  - activity: a human-readable log of what Alex did (tool calls, wake events, errors)
"""

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from config.settings import data_dir


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    """Thin, thread-safe wrapper around a single SQLite file."""

    def __init__(self, path: Path = None):
        self.path = path or (data_dir() / "alex.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()

    def _init_schema(self):
        with self._lock, self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    # ---------------------------------------------------------- memories --
    def add_memory(self, content: str) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO memories (content, created_at) VALUES (?, ?)",
                (content.strip(), _now()),
            )
            return cur.lastrowid

    def get_memories(self):
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, content, created_at FROM memories ORDER BY id DESC"
            )
            return [dict(id=r[0], content=r[1], created_at=r[2]) for r in cur.fetchall()]

    def search_memories(self, query: str):
        query = (query or "").strip().lower()
        if not query:
            return self.get_memories()
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, content, created_at FROM memories WHERE lower(content) LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
            )
            return [dict(id=r[0], content=r[1], created_at=r[2]) for r in cur.fetchall()]

    def delete_memory(self, memory_id: int):
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

    def clear_memories(self):
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM memories")

    # ------------------------------------------------------- conversation --
    def add_message(self, role: str, content: str):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO conversation (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, _now()),
            )

    def get_recent_messages(self, limit: int = 10):
        """Returns the last `limit` messages, oldest first, as [{role, content}]."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT role, content FROM conversation ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        rows.reverse()
        return [dict(role=r[0], content=r[1]) for r in rows]

    def clear_conversation(self):
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM conversation")

    # ------------------------------------------------------------ activity --
    def log_activity(self, event: str, detail: str = ""):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO activity (event, detail, created_at) VALUES (?, ?, ?)",
                (event, detail, _now()),
            )

    def get_activity(self, limit: int = 200):
        with self._lock:
            cur = self._conn.execute(
                "SELECT event, detail, created_at FROM activity ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(event=r[0], detail=r[1], created_at=r[2]) for r in cur.fetchall()]

    def close(self):
        with self._lock:
            self._conn.close()
