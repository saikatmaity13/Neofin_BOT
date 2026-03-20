"""
In-memory conversation store for NeoStats Credit Underwriter.
Each session_id maps to an ordered list of message dicts.
"""

from collections import defaultdict, deque
from typing import Dict, List

MAX_TURNS = 30  # keep last 30 turns per session


class MemoryManager:
    def __init__(self, max_turns: int = MAX_TURNS):
        self._max = max_turns * 2  # user + assistant pairs
        self._store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self._max))

    def get_history(self, session_id: str) -> List[dict]:
        return list(self._store[session_id])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self._store[session_id].append({"role": role, "content": content})

    def clear(self, session_id: str) -> None:
        self._store[session_id].clear()

    def session_length(self, session_id: str) -> int:
        return len(self._store[session_id])


memory_manager = MemoryManager()
