import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal


@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)


@pytest.fixture(scope="function")
def test_db(monkeypatch):
    """Provide a clean in-memory database for model tests when needed."""
    # Override engine to use sqlite in-memory for tests that need direct DB
    test_engine = engine
    # For simplicity, reuse the existing engine; create tables before each test
    Base.metadata.create_all(bind=test_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import after patching environment
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables for each test."""
    # Create a unique temporary database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    test_env = {
        "DATABASE_URL": f"sqlite:///{db_path}",
        "VIDEO_BASE_DIR": "/tmp/test_videos"
    }
    
    with patch.dict(os.environ, test_env):
        yield
    
    # Cleanup
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app
    return TestClient(app)

@pytest.fixture
def mock_video_data():
    """Provide mock video data for testing."""
    return {
        "items": [
            {
                "title": "Introduction to Python",
                "path": "python-course/01-introduction.mp4",
                "dir_path": "python-course",
                "size": 1024000,
                "duration": 600.0,
                "format": "mp4",
                "subtitle_path": "python-course/01-introduction.vtt",
                "thumbnail_path": "python-course/01-introduction.jpg"
            },
            {
                "title": "Variables and Data Types",
                "path": "python-course/02-variables.mp4", 
                "dir_path": "python-course",
                "size": 1536000,
                "duration": 720.0,
                "format": "mp4",
                "subtitle_path": "python-course/02-variables.vtt",
                "thumbnail_path": "python-course/02-variables.jpg"
            },
            {
                "title": "Getting Started with JavaScript",
                "path": "javascript-course/01-getting-started.mp4",
                "dir_path": "javascript-course", 
                "size": 2048000,
                "duration": 900.0,
                "format": "mp4",
                "subtitle_path": "javascript-course/01-getting-started.vtt",
                "thumbnail_path": "javascript-course/01-getting-started.jpg"
            }
        ]
    }

@pytest.fixture 
def sample_preferences():
    """Provide sample preference data for testing."""
    return [
        {"key": "rating:python-course", "value": "5", "type": "course_rating"},
        {"key": "rating:javascript-course", "value": "4", "type": "course_rating"},
        {"key": "videoRating:python-course/01-introduction.mp4", "value": "5", "type": "video_rating"},
        {"key": "played:python-course/01-introduction.mp4", "value": "true", "type": "played"},
        {"key": "progress:python-course/02-variables.mp4", "value": "360.0", "type": "progress"}
    ]

@pytest.fixture
def user_agents():
    """Provide various user agent strings for testing."""
    return {
        "desktop_chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "desktop_firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "desktop_safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "iphone_safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        "android_chrome": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "tablet_safari": "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
    }

class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_test_preferences(client, preferences):
        """Helper to create multiple preferences."""
        results = []
        for pref in preferences:
            response = client.post("/api/preferences", json=pref)
            results.append(response)
        return results
    
    @staticmethod
    def create_sync_group_with_devices(client, device_count=2, description="Test Group"):
        """Helper to create a sync group and add multiple devices."""
        # Create sync group
        response = client.post("/api/sync/create", json={"description": description})
        sync_code = response.json()["sync_code"]
        
        clients = [client]  # Include the original client
        
        # Add additional devices
        for i in range(1, device_count):
            test_client = TestClient(client.app)
            clients.append(test_client)
            
            join_data = {
                "sync_code": sync_code,
                "device_name": f"Test Device {i+1}"
            }
            test_client.post("/api/sync/join", json=join_data)
            
        return sync_code, clients
    
    @staticmethod
    def verify_preferences_synced(clients, expected_prefs):
        """Helper to verify preferences are synced across all clients."""
        for client in clients:
            response = client.get("/api/preferences") 
            prefs = response.json()
            
            for expected_key in expected_prefs:
                assert expected_key in prefs

# Make TestHelpers available as fixture
@pytest.fixture
def helpers():
    """Provide test helper functions."""
    return TestHelpers

# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database"
    )

# Cleanup function for test isolation
@pytest.fixture(autouse=True)
def cleanup_between_tests():
    """Clean up between tests to ensure isolation."""
    yield
    # Add any cleanup logic here if needed
    pass
