import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestCoreAPI:
    """Test suite for core API functionality (streamlined for speed)."""
    
    def test_root_redirect(self):
        """Test that root serves the main page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_static_files(self):
        """Test that static files are served correctly."""
        response = client.get("/static/index.html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_api_library_endpoint(self):
        """Test the /api/library endpoint."""
        response = client.get("/api/library")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestSecurity:
    """Test basic security measures."""
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks (video route)."""
        response = client.get("/video/../../../etc/passwd")
        assert response.status_code in (404, 416)
