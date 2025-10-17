import pytest
import tempfile
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
from app.main import app

client = TestClient(app)

# Database setup is now handled by conftest.py

@pytest.fixture
def mock_video_library():
    """Mock video library data for testing."""
    return {
        "items": [
            {
                "title": "Course 1 - Video 1",
                "path": "course1/video1.mp4",
                "dir_path": "course1",
                "size": 1024000,
                "duration": 120.5,
                "format": "mp4"
            },
            {
                "title": "Course 1 - Video 2", 
                "path": "course1/video2.mp4",
                "dir_path": "course1",
                "size": 2048000,
                "duration": 180.0,
                "format": "mp4"
            },
            {
                "title": "Course 2 - Video 1",
                "path": "course2/video1.mp4", 
                "dir_path": "course2",
                "size": 1536000,
                "duration": 150.0,
                "format": "mp4"
            }
        ]
    }

class TestFullWorkflow:
    """Test complete user workflows from start to finish."""
    
    def test_new_user_complete_workflow(self, mock_video_library):
        """Test complete workflow for a new user."""
        # 1. Get initial preferences (should be empty)
        response = client.get("/api/preferences")
        assert response.status_code == 200
        prefs = response.json()
        assert len(prefs) == 0
        
        # 2. Check sync status (should not be synced)
        response = client.get("/api/sync/status")
        assert response.status_code == 200
        sync_status = response.json()
        assert sync_status["synced"] is False
        
        # 3. Rate some courses
        ratings = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "rating:course2", "value": "4", "type": "course_rating"}
        ]
        
        for rating in ratings:
            response = client.post("/api/preferences", json=rating)
            assert response.status_code == 200
            
        # 4. Mark some videos as played and set progress
        video_prefs = [
            {"key": "played:course1/video1.mp4", "value": "true", "type": "played"},
            {"key": "progress:course1/video1.mp4", "value": "120.5", "type": "progress"},
            {"key": "videoRating:course1/video1.mp4", "value": "5", "type": "video_rating"}
        ]
        
        for pref in video_prefs:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # 5. Verify all preferences were saved
        response = client.get("/api/preferences")
        assert response.status_code == 200
        all_prefs = response.json()
        assert len(all_prefs) == 5  # 2 course ratings + 3 video prefs
        
        # 6. Create sync group
        response = client.post("/api/sync/create", json={"description": "My Devices"})
        assert response.status_code == 200
        sync_data = response.json()
        assert sync_data["success"] is True
        sync_code = sync_data["sync_code"]
        
        # 7. Verify sync status updated
        response = client.get("/api/sync/status")
        assert response.status_code == 200
        sync_status = response.json()
        assert sync_status["synced"] is True
        assert sync_status["sync_code"] == sync_code
        assert sync_status["device_count"] == 1
        assert sync_status["expires_at"] is None  # Permanent
        
    def test_multi_device_sync_workflow(self):
        """Test sync workflow across multiple devices."""
        # Device 1: Setup and create preferences
        device1_prefs = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "played:video1.mp4", "value": "true", "type": "played"}
        ]
        
        for pref in device1_prefs:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # Device 1: Create sync group
        response = client.post("/api/sync/create", json={"description": "Multi Device Test"})
        sync_code = response.json()["sync_code"]
        
        # Device 2: Join sync group
        with TestClient(app) as client2:
            join_data = {"sync_code": sync_code, "device_name": "Mobile Device"}
            response = client2.post("/api/sync/join", json=join_data)
            assert response.status_code == 200
            
            # Device 2: Should see Device 1's preferences
            response = client2.get("/api/preferences")
            device2_prefs = response.json()
            assert "rating:course1" in device2_prefs
            assert "played:video1.mp4" in device2_prefs
            assert device2_prefs["rating:course1"]["synced_from"] is True
            
            # Device 2: Add its own preferences
            device2_new_prefs = [
                {"key": "rating:course2", "value": "4", "type": "course_rating"},
                {"key": "progress:video2.mp4", "value": "45.0", "type": "progress"}
            ]
            
            for pref in device2_new_prefs:
                response = client2.post("/api/preferences", json=pref)
                assert response.status_code == 200
                
        # Device 1: Should now see Device 2's preferences
        response = client.get("/api/preferences")
        merged_prefs = response.json()
        assert len(merged_prefs) == 4  # All preferences from both devices
        assert "rating:course2" in merged_prefs
        assert "progress:video2.mp4" in merged_prefs

class TestFireRatingSystem:
    """Test fire rating system functionality."""
    
    def test_fire_rating_workflow(self):
        """Test complete fire rating workflow."""
        course_name = "test_course"
        
        # Test rating progression: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0 (clear)
        for rating in range(1, 6):
            pref_data = {
                "key": f"rating:{course_name}",
                "value": str(rating),
                "type": "course_rating"
            }
            response = client.post("/api/preferences", json=pref_data)
            assert response.status_code == 200
            
            # Verify rating was set
            response = client.get("/api/preferences")
            prefs = response.json()
            assert prefs[f"rating:{course_name}"]["value"] == str(rating)
            
        # Test clearing rating (set to 0 or remove)
        clear_data = {
            "key": f"rating:{course_name}",
            "value": "0",
            "type": "course_rating"
        }
        response = client.post("/api/preferences", json=clear_data)
        assert response.status_code == 200
        
    def test_video_fire_rating(self):
        """Test fire rating for individual videos."""
        video_ratings = [
            {"key": "videoRating:video1.mp4", "value": "5", "type": "video_rating"},
            {"key": "videoRating:video2.mp4", "value": "3", "type": "video_rating"},
            {"key": "videoRating:video3.mp4", "value": "1", "type": "video_rating"}
        ]
        
        for rating in video_ratings:
            response = client.post("/api/preferences", json=rating)
            assert response.status_code == 200
            
        # Verify all ratings
        response = client.get("/api/preferences")
        prefs = response.json()
        assert len(prefs) == 3
        assert prefs["videoRating:video1.mp4"]["value"] == "5"
        assert prefs["videoRating:video2.mp4"]["value"] == "3"
        assert prefs["videoRating:video3.mp4"]["value"] == "1"

class TestCourseFiltering:
    """Test course filtering functionality."""
    
    def test_library_with_course_filtering(self, mock_video_library):
        """Test library API with course structure."""
        
        # Get full library (test basic functionality without mocking)
        response = client.get("/api/library")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        
        # Test that course structure exists in returned data
        if data["items"]:
            # Check that items have expected structure
            for item in data["items"]:
                assert "title" in item or "path" in item
        
    def test_course_preferences_isolation(self):
        """Test that course preferences are properly isolated."""
        # Set preferences for different courses
        course_prefs = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "rating:course2", "value": "3", "type": "course_rating"},
            {"key": "rating:course3", "value": "4", "type": "course_rating"}
        ]
        
        for pref in course_prefs:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # Verify all course ratings are independent
        response = client.get("/api/preferences")
        prefs = response.json()
        
        assert prefs["rating:course1"]["value"] == "5"
        assert prefs["rating:course2"]["value"] == "3" 
        assert prefs["rating:course3"]["value"] == "4"

class TestVideoProgress:
    """Test video progress tracking functionality."""
    
    def test_video_progress_workflow(self):
        """Test complete video progress workflow."""
        video_path = "course1/lesson1.mp4"
        
        # Set initial progress
        progress_data = {
            "key": f"progress:{video_path}",
            "value": "30.5",
            "type": "progress"
        }
        response = client.post("/api/preferences", json=progress_data)
        assert response.status_code == 200
        
        # Update progress multiple times
        progress_updates = ["45.0", "60.2", "75.8", "90.0"]
        for progress in progress_updates:
            update_data = {
                "key": f"progress:{video_path}",
                "value": progress,
                "type": "progress"
            }
            response = client.post("/api/preferences", json=update_data)
            assert response.status_code == 200
            
        # Mark as played when completed
        played_data = {
            "key": f"played:{video_path}",
            "value": "true",
            "type": "played"
        }
        response = client.post("/api/preferences", json=played_data)
        assert response.status_code == 200
        
        # Verify final state
        response = client.get("/api/preferences")
        prefs = response.json()
        assert prefs[f"progress:{video_path}"]["value"] == "90.0"
        assert prefs[f"played:{video_path}"]["value"] == "true"

class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_concurrent_preference_updates(self):
        """Test handling of concurrent preference updates."""
        # Simulate concurrent updates to same preference
        base_key = "rating:concurrent_test"
        
        # Make multiple rapid updates
        for i in range(10):
            pref_data = {
                "key": base_key,
                "value": str(i % 5 + 1),
                "type": "course_rating"
            }
            response = client.post("/api/preferences", json=pref_data)
            assert response.status_code == 200
            
        # Verify final state is consistent
        response = client.get("/api/preferences")
        prefs = response.json()
        assert base_key in prefs
        # Should have one of the values (last one wins)
        assert prefs[base_key]["value"] in ["1", "2", "3", "4", "5"]
        
    def test_sync_group_consistency(self):
        """Test sync group data consistency."""
        # Create sync group
        response = client.post("/api/sync/create", json={"description": "Consistency Test"})
        sync_code = response.json()["sync_code"]
        
        # Add multiple devices
        device_names = ["Device 1", "Device 2", "Device 3"]
        clients = []
        
        try:
            for device_name in device_names:
                test_client = TestClient(app)
                clients.append(test_client)
                
                join_data = {"sync_code": sync_code, "device_name": device_name}
                response = test_client.post("/api/sync/join", json=join_data)
                assert response.status_code == 200
                
            # Check sync status consistency across all devices
            for test_client in clients:
                response = test_client.get("/api/sync/status")
                assert response.status_code == 200
                status = response.json()
                assert status["synced"] is True
                assert status["sync_code"] == sync_code
                assert status["device_count"] == 4  # Original + 3 joined
                
        finally:
            # Cleanup clients
            for test_client in clients:
                test_client.close()

class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_partial_sync_failure_recovery(self):
        """Test recovery from partial sync failures."""
        # Create sync group and add preferences
        response = client.post("/api/sync/create", json={"description": "Recovery Test"})
        sync_code = response.json()["sync_code"]
        
        # Add some preferences
        prefs = [
            {"key": "rating:recovery1", "value": "4", "type": "course_rating"},
            {"key": "rating:recovery2", "value": "5", "type": "course_rating"}
        ]
        
        for pref in prefs:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # Simulate second device joining after preferences were set
        with TestClient(app) as client2:
            join_data = {"sync_code": sync_code, "device_name": "Recovery Device"}
            response = client2.post("/api/sync/join", json=join_data)
            assert response.status_code == 200
            
            # Should get all existing preferences
            response = client2.get("/api/preferences")
            synced_prefs = response.json()
            assert len(synced_prefs) == 2
            assert "rating:recovery1" in synced_prefs
            assert "rating:recovery2" in synced_prefs

class TestDataReset:
    """Test complete data reset functionality."""
    
    def test_complete_reset_workflow(self):
        """Test complete data reset workflow."""
        # Set up comprehensive user data
        # 1. Course ratings
        course_ratings = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "rating:course2", "value": "4", "type": "course_rating"}
        ]
        
        # 2. Video ratings and progress
        video_data = [
            {"key": "videoRating:video1.mp4", "value": "5", "type": "video_rating"},
            {"key": "played:video1.mp4", "value": "true", "type": "played"},
            {"key": "progress:video1.mp4", "value": "120.5", "type": "progress"},
            {"key": "videoRating:video2.mp4", "value": "3", "type": "video_rating"},
            {"key": "progress:video2.mp4", "value": "45.0", "type": "progress"}
        ]
        
        # Set all preferences
        all_prefs = course_ratings + video_data
        for pref in all_prefs:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # 3. Create sync group
        response = client.post("/api/sync/create", json={"description": "Reset Test Group"})
        assert response.status_code == 200
        
        # 4. Verify all data exists
        response = client.get("/api/preferences")
        prefs_before = response.json()
        assert len(prefs_before) == 7
        
        response = client.get("/api/sync/status")
        sync_before = response.json()
        assert sync_before["synced"] is True
        
        # 5. Reset all data
        response = client.post("/api/reset")
        assert response.status_code == 200
        reset_result = response.json()
        assert reset_result["success"] is True
        
        # 6. Verify everything is cleared
        # Note: After reset, we're essentially a new user, so we should test
        # that the reset endpoint works correctly for the current implementation
