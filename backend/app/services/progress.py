from datetime import datetime, timezone
from threading import Lock
from uuid import UUID


class ProgressStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._states: dict[str, dict] = {}

    def start(self, session_id: UUID, stage: str = "Sesja utworzona", progress: int = 0) -> None:
        self.update(session_id, progress=progress, stage=stage, status="created")

    def update(self, session_id: UUID, progress: int, stage: str, status: str = "processing") -> None:
        safe_progress = max(0, min(100, int(progress)))
        with self._lock:
            self._states[str(session_id)] = {
                "progress": safe_progress,
                "stage": stage,
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            }

    def complete(self, session_id: UUID, stage: str = "Analiza zakończona") -> None:
        self.update(session_id, progress=100, stage=stage, status="completed")

    def fail(self, session_id: UUID, stage: str = "Analiza nieudana") -> None:
        self.update(session_id, progress=100, stage=stage, status="failed")

    def get(self, session_id: UUID) -> dict | None:
        with self._lock:
            state = self._states.get(str(session_id))
            if not state:
                return None
            return dict(state)

    def clear(self, session_id: UUID) -> None:
        with self._lock:
            self._states.pop(str(session_id), None)


progress_store = ProgressStore()
