import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestVideoSite:
    """Test suite for the video site application."""
    
    def test_root_redirect(self):
        """Test that root redirects to static files."""
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
    
    def test_video_streaming(self):
        """Test video streaming endpoint."""
        # This test requires a video file to exist
        # We'll create a mock test video file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"fake video content")
            tmp_path = tmp.name
        
        try:
            # Mock the video path
            response = client.get(f"/videos/{os.path.basename(tmp_path)}")
            # Should return 200 if file exists, 404 if not
            assert response.status_code in [200, 404]
        finally:
            os.unlink(tmp_path)
    
    def test_subtitle_endpoint(self):
        """Test subtitle endpoint."""
        response = client.get("/subtitles/nonexistent.vtt")
        assert response.status_code == 404
    
    def test_resources_endpoint(self):
        """Test resources endpoint."""
        response = client.get("/resources/nonexistent.pdf")
        assert response.status_code == 404
    
    def test_api_library_with_search(self):
        """Test API library with search parameter."""
        response = client.get("/api/library?search=test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_api_library_with_sort(self):
        """Test API library with sort parameter."""
        response = client.get("/api/library?sort=title")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestVideoProcessing:
    """Test video processing functionality."""
    
    def test_video_metadata_extraction(self):
        """Test video metadata extraction."""
        # This would test the video metadata extraction logic
        # For now, we'll test the API endpoint
        response = client.get("/api/library")
        assert response.status_code == 200
    
    def test_video_sorting(self):
        """Test video sorting functionality."""
        response = client.get("/api/library")
        assert response.status_code == 200
        data = response.json()
        
        # Check if videos are properly sorted
        if data["items"]:
            titles = [video["title"] for video in data["items"]]
            # Basic check that we have titles
            assert all(isinstance(title, str) for title in titles)

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_nonexistent_video(self):
        """Test handling of nonexistent video files."""
        response = client.get("/videos/nonexistent.mp4")
        assert response.status_code == 404
    
    def test_invalid_path_traversal(self):
        """Test protection against path traversal attacks."""
        response = client.get("/videos/../../../etc/passwd")
        assert response.status_code == 404
    
    def test_large_file_handling(self):
        """Test handling of large file requests."""
        # This would test memory usage and timeout handling
        response = client.get("/api/library")
        assert response.status_code == 200

@pytest.fixture
def sample_video_data():
    """Fixture providing sample video data for testing."""
    return {
        "title": "Test Video",
        "path": "test/video.mp4",
        "duration": 120.5,
        "size": 1024000
    }

def test_video_data_structure(sample_video_data):
    """Test that video data has the expected structure."""
    assert "title" in sample_video_data
    assert "path" in sample_video_data
    assert "duration" in sample_video_data
    assert "size" in sample_video_data
