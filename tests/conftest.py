import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app import database as db_mod


@pytest.fixture(scope="function", autouse=True)
def fast_in_memory_db(monkeypatch):
    """Use a fresh in-memory SQLite DB per test to avoid file I/O and state bleed."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_mod.Base.metadata.create_all(bind=engine)

    def get_test_db():
        test_db = TestingSessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    # Override engine/session dependency everywhere
    monkeypatch.setattr(db_mod, "engine", engine, raising=True)
    monkeypatch.setattr(db_mod, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr("app.main.get_db", get_test_db, raising=True)
    yield


@pytest.fixture(scope="function")
def test_db():
    """Direct DB access fixture for model-level tests."""
    SessionLocal = db_mod.SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FakeCoordinator:
    def __init__(self):
        self._tasks = {}
        self._summaries = {}

    def start_video_summary(self, video_path: str, user_id=None, force=False):
        if not video_path:
            return {"success": False, "error": "Invalid video path"}
        if (video_path in self._summaries) and not force:
            return {"success": False, "error": "Summary already exists", "existing_summary": {"status": "completed", "summary": self._summaries[video_path]}}
        task_id = f"task_{len(self._tasks)+1}"
        self._tasks[task_id] = {"status": "processing", "progress": "Queued", "progress_percent": 0}
        # complete immediately for speed
        self._tasks[task_id].update({"status": "completed", "progress": "Done", "progress_percent": 100})
        self._summaries[video_path] = "This is a generated summary."
        return {"success": True, "task_id": task_id, "status": "processing", "message": "Started"}

    def get_summary_status(self, task_id: str):
        return self._tasks.get(task_id)

    def get_video_summary(self, video_path: str):
        if video_path in self._summaries:
            return {"video_path": video_path, "summary": self._summaries[video_path], "status": "completed", "generated_at": "2025-01-01T00:00:00"}
        return None

    def delete_video_summary(self, video_path: str):
        existed = self._summaries.pop(video_path, None)
        if existed:
            return {"success": True, "message": "Summary deleted"}
        return {"success": False, "error": "Summary not found"}

    def list_video_summaries(self, status=None, limit=100):
        return [{"video_path": vp, "status": "completed", "generated_at": "2025-01-01T00:00:00", "has_summary": True} for vp in list(self._summaries)[:limit]]

    def get_summary_statistics(self):
        total = len(self._summaries)
        return {"total_summaries": total, "completed": total, "failed": 0, "processing": 0, "average_processing_time": 0.0, "status_breakdown": {"completed": total}}


# Use this fixture explicitly in tests that need fast AI; don't autouse so that
# tests that check unavailable services can work as written.
@pytest.fixture()
def fake_ai(monkeypatch):
    fake = FakeCoordinator()
    monkeypatch.setattr("app.ai_summary.coordinator.get_coordinator", lambda: fake, raising=True)
    yield


@pytest.fixture(scope="function", autouse=True)
def deterministic_sync_code(monkeypatch):
    counter = {"n": 0}
    def next_code():
        counter["n"] += 1
        n = counter["n"]
        return f"TS{n:04d}"  # TS0001, TS0002, ...
    monkeypatch.setattr("app.sync_system.generate_sync_code", next_code, raising=True)
    yield


@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)
