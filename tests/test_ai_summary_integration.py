"""
Fast integration tests for AI Summary system (all mocked)
Updated to work with lazy loading coordinator pattern
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestAISummaryIntegration:
    """Integration tests for the complete AI summary workflow"""

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_complete_summary_workflow_success(self, mock_get_coordinator, test_client):
        """Test complete workflow from video to summary"""
        # Setup mock coordinator
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

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_workflow_with_failure(self, mock_get_coordinator, test_client):
        """Test workflow when AI processing fails"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': False,
            'error': 'Video file not found: /app/data/course1/no_audio.mp4'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/course1/no_audio.mp4"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'Video file not found' in data['detail']

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_duplicate_summary_prevention(self, mock_get_coordinator, test_client):
        """Test that duplicate summaries are prevented"""
        mock_coordinator = MagicMock()
        mock_coordinator.start_video_summary.return_value = {
            'success': False,
            'error': 'Summary already exists',
            'existing_summary': {
                'summary': 'Existing summary content',
                'status': 'completed',
                'generated_at': '2025-10-18T10:00:00Z'
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
        assert 'already exists' in data['error']
        assert data['existing_summary']['status'] == 'completed'

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_summary_status_tracking(self, mock_get_coordinator, test_client):
        """Test status tracking throughout the workflow"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_summary_status.return_value = {
            'status': 'processing',
            'progress': 'Currently transcribing audio',
            'progress_percent': 50,
            'task_id': 'task_123'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/summary-status/task_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'processing'
        assert data['progress_percent'] == 50

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_get_video_summary(self, mock_get_coordinator, test_client):
        """Test retrieving completed video summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_video_summary.return_value = {
            'video_path': '/app/data/course1/video1.mp4',
            'summary': 'This is a comprehensive summary...',
            'status': 'completed',
            'generated_at': '2025-10-18T10:00:00Z',
            'model_used': 'whisper-base+llama3.2:7b'
        }
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summary/course1/video1.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data['summary'] == 'This is a comprehensive summary...'
        assert data['status'] == 'completed'

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_video_summary_not_found(self, mock_get_coordinator, test_client):
        """Test retrieving non-existent video summary"""
        mock_coordinator = MagicMock()
        mock_coordinator.get_video_summary.return_value = None
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summary/course1/nonexistent.mp4")
        
        assert response.status_code == 404
        data = response.json()
        assert 'Summary not found' in data['detail']

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_ai_service_unavailable(self, mock_get_coordinator, test_client):
        """Test behavior when AI services are unavailable"""
        # Mock coordinator not available (returns None)
        mock_get_coordinator.return_value = None
        
        response = test_client.post(
            "/api/generate-summary",
            json={"video_path": "/app/data/course1/video1.mp4"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert 'AI summary features are currently unavailable' in data['detail']

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_list_video_summaries(self, mock_get_coordinator, test_client):
        """Test listing all video summaries"""
        mock_coordinator = MagicMock()
        mock_coordinator.list_video_summaries.return_value = [
            {
                'video_path': '/app/data/course1/video1.mp4',
                'status': 'completed',
                'summary': 'Summary 1...'
            },
            {
                'video_path': '/app/data/course1/video2.mp4',
                'status': 'processing',
                'summary': None
            }
        ]
        mock_get_coordinator.return_value = mock_coordinator
        
        response = test_client.get("/api/video-summaries")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['status'] == 'completed'
        assert data[1]['status'] == 'processing'

    def test_ai_health_without_services(self, test_client):
        """Test AI health check when services are unavailable"""
        # Without patching, get_coordinator returns None due to lazy loading
        response = test_client.get("/api/ai-health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['overall_status'] == 'unavailable'
        assert data['ollama']['status'] == 'unavailable'
        assert data['whisper']['status'] == 'unavailable'
        assert data['ffmpeg']['status'] == 'unavailable'

    @patch('app.ai_summary.coordinator.get_coordinator')
    def test_summary_statistics(self, mock_get_coordinator, test_client):
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
        assert data['completed_summaries'] == 30
        assert data['average_processing_time'] == 120.5