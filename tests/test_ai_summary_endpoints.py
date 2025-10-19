"""
Test AI Summary API endpoints with proper mocking for lazy loading
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestAISummaryEndpoints:
    """Test AI Summary API endpoints with mocked services"""

    @patch('app.main.get_coordinator')
    def test_generate_summary_endpoint_success(self, mock_get_coordinator, test_client):
        """Test successful summary generation request"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': True,
            'task_id': 'task_123',
            'status': 'processing',
            'message': 'Summary generation started'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/course1/video1.mp4"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['task_id'] == 'task_123'
        assert data['status'] == 'processing'

    @patch('app.main.get_coordinator')
    def test_generate_summary_invalid_video_path(self, mock_get_coordinator, test_client):
        """Test summary generation with invalid video path"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': False,
            'error': 'Invalid video path'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'video_path' in data['detail'].lower() or 'invalid' in data['detail'].lower()

    @patch('app.main.get_coordinator')
    def test_generate_summary_nonexistent_video(self, mock_get_coordinator, test_client):
        """Test summary generation for non-existent video"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': False,
            'error': 'Video file not found: /app/data/nonexistent.mp4'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/nonexistent.mp4"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'not found' in data['detail'].lower()

    @patch('app.main.get_coordinator')
    def test_generate_summary_duplicate_request(self, mock_get_coordinator, test_client):
        """Test duplicate summary generation request"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': False,
            'error': 'Summary already exists or is being processed',
            'existing_summary': {
                'status': 'completed',
                'summary': 'Existing summary content'
            }
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/course1/video1.mp4"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert 'already exists' in data['error'].lower()
        assert data['existing_summary']['status'] == 'completed'

    @patch('app.main.get_coordinator')
    def test_check_summary_status_endpoint(self, mock_get_coordinator, test_client):
        """Test checking summary generation status"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_summary_status.return_value = {
            'status': 'processing',
            'progress': 'Extracting audio',
            'progress_percent': 50
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/summary-status/task_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'processing'
        assert data['progress_percent'] == 50

    @patch('app.main.get_coordinator')
    def test_check_summary_status_task_not_found(self, mock_get_coordinator, test_client):
        """Test checking status for non-existent task"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_summary_status.return_value = None
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/summary-status/non_existent_task")
        
        assert response.status_code == 404
        data = response.json()
        assert 'Task not found' in data['detail']

    @patch('app.main.get_coordinator')
    def test_get_video_summary_endpoint(self, mock_get_coordinator, test_client):
        """Test getting completed video summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_video_summary.return_value = {
            'video_path': '/app/data/course1/video1.mp4',
            'summary': 'This is a generated summary.',
            'status': 'completed',
            'generated_at': '2025-01-01T12:00:00'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summary/course1/video1.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data['summary'] == 'This is a generated summary.'
        assert data['status'] == 'completed'

    @patch('app.main.get_coordinator')
    def test_get_video_summary_not_found(self, mock_get_coordinator, test_client):
        """Test getting summary for video without summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_video_summary.return_value = None
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summary/course1/nonexistent.mp4")
        
        assert response.status_code == 404
        data = response.json()
        assert 'Summary not found' in data['detail']

    @patch('app.main.get_coordinator')
    def test_get_video_summary_failed_generation(self, mock_get_coordinator, test_client):
        """Test getting summary for failed generation"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_video_summary.return_value = {
            'video_path': '/app/data/course1/no_audio.mp4',
            'summary': None,
            'status': 'failed',
            'error_message': 'No audio track found'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summary/course1/no_audio.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'failed'
        assert 'No audio track found' in data['error_message']

    @patch('app.main.get_coordinator')
    def test_list_video_summaries_endpoint(self, mock_get_coordinator, test_client):
        """Test listing all video summaries"""
        mock_coordinator = MagicMock()
        mock_coordinator.list_video_summaries.return_value = [
            {'video_path': '/v1.mp4', 'status': 'completed', 'summary': 'Sum1'},
            {'video_path': '/v2.mp4', 'status': 'processing', 'summary': None}
        ]
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summaries")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['video_path'] == '/v1.mp4'

    @patch('app.main.get_coordinator')
    def test_delete_video_summary_endpoint(self, mock_get_coordinator, test_client):
        """Test deleting a video summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.delete_video_summary.return_value = {
            'success': True,
            'message': 'Summary deleted'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.delete(
            "/api/delete-summary/course1/video1.mp4"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'deleted' in data['message'].lower()

    @patch('app.main.get_coordinator')
    def test_delete_video_summary_not_found(self, mock_get_coordinator, test_client):
        """Test deleting non-existent summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.delete_video_summary.return_value = {
            'success': False,
            'message': 'Summary not found'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.delete(
            "/api/delete-summary/course1/nonexistent.mp4"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'not found' in data['detail'].lower()

    @patch('app.main.get_coordinator')
    def test_summary_statistics_endpoint(self, mock_get_coordinator, test_client):
        """Test getting summary generation statistics"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_summary_statistics.return_value = {
            'total_summaries': 45,
            'completed_summaries': 30,
            'failed_summaries': 5,
            'processing_summaries': 10,
            'average_processing_time': 120.5
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/summary-statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_summaries'] == 45

    def test_ai_service_health_check_unavailable(self, test_client):
        """Test AI services health check when unavailable"""
        # Without mocking, get_coordinator returns None due to lazy loading
        response = test_client.get("/api/ai-health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['overall_status'] == 'unavailable'
        assert data['ollama']['status'] == 'unavailable'

    def test_ai_service_unavailable_generate_summary(self, test_client):
        """Test generate summary when AI services unavailable"""
        # Without mocking, get_coordinator returns None
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/course1/video1.mp4"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert 'AI summary features are currently unavailable' in data['detail']