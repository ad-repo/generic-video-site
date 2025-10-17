import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

# Create test client
client = TestClient(app)

# Database setup is now handled by conftest.py

class TestPreferencesAPI:
    """Test preferences API endpoints."""
    
    def test_get_preferences_empty(self):
        """Test getting preferences when none exist."""
        response = client.get("/api/preferences")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should be empty for new user
        
    def test_set_preference_success(self):
        """Test setting a preference successfully."""
        preference_data = {
            "key": "rating:test_course",
            "value": "4",
            "type": "course_rating"
        }
        
        response = client.post("/api/preferences", json=preference_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["key"] == "rating:test_course"
        
    def test_set_preference_validation(self):
        """Test preference validation."""
        # Missing required fields
        invalid_data = {
            "key": "test_key"
            # Missing value and type
        }
        
        response = client.post("/api/preferences", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
    def test_get_preferences_after_setting(self):
        """Test getting preferences after setting some."""
        # Set multiple preferences
        preferences = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "videoRating:video1", "value": "4", "type": "video_rating"},
            {"key": "played:video1", "value": "true", "type": "played"},
            {"key": "progress:video1", "value": "42.5", "type": "progress"}
        ]
        
        for pref in preferences:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # Get all preferences
        response = client.get("/api/preferences")
        assert response.status_code == 200
        data = response.json()
        
        # Should have all 4 preferences
        assert len(data) == 4
        
        # Check specific preferences
        assert "rating:course1" in data
        assert data["rating:course1"]["value"] == "5"
        assert data["rating:course1"]["type"] == "course_rating"
        
    def test_update_preference(self):
        """Test updating an existing preference."""
        # Set initial preference
        initial_pref = {
            "key": "rating:update_test",
            "value": "3",
            "type": "course_rating"
        }
        response = client.post("/api/preferences", json=initial_pref)
        assert response.status_code == 200
        
        # Update the preference
        updated_pref = {
            "key": "rating:update_test",
            "value": "5",
            "type": "course_rating"
        }
        response = client.post("/api/preferences", json=updated_pref)
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/api/preferences")
        data = response.json()
        assert data["rating:update_test"]["value"] == "5"

class TestSyncAPI:
    """Test sync API endpoints."""
    
    def test_sync_status_not_synced(self):
        """Test sync status when not synced."""
        response = client.get("/api/sync/status")
        assert response.status_code == 200
        data = response.json()
        assert data["synced"] is False
        assert "message" in data
        
    def test_create_sync_group(self):
        """Test creating a sync group."""
        group_data = {"description": "Test Sync Group"}
        
        response = client.post("/api/sync/create", json=group_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "sync_code" in data
        assert len(data["sync_code"]) == 6
        assert "message" in data
        
    def test_create_sync_group_no_description(self):
        """Test creating sync group without description."""
        response = client.post("/api/sync/create", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
    def test_sync_status_after_creation(self):
        """Test sync status after creating a group."""
        # Create sync group
        response = client.post("/api/sync/create", json={"description": "Status Test"})
        assert response.status_code == 200
        sync_data = response.json()
        sync_code = sync_data["sync_code"]
        
        # Check sync status
        response = client.get("/api/sync/status")
        assert response.status_code == 200
        data = response.json()
        
        assert data["synced"] is True
        assert data["sync_code"] == sync_code
        assert data["device_count"] == 1
        assert len(data["devices"]) == 1
        assert data["expires_at"] is None  # Permanent sync
        
    def test_join_sync_group_success(self):
        """Test joining a sync group successfully."""
        # First, create a sync group with one client
        response = client.post("/api/sync/create", json={"description": "Join Test"})
        sync_data = response.json()
        sync_code = sync_data["sync_code"]
        
        # Create a new client session (simulate different device)
        with TestClient(app) as client2:
            join_data = {
                "sync_code": sync_code,
                "device_name": "Test Device 2"
            }
            
            response = client2.post("/api/sync/join", json=join_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
    def test_join_invalid_sync_group(self):
        """Test joining an invalid sync group."""
        join_data = {
            "sync_code": "INVALID",
            "device_name": "Test Device"
        }
        
        response = client.post("/api/sync/join", json=join_data)
        assert response.status_code == 200  # Returns 200 but success=False
        data = response.json()
        assert data["success"] is False
        assert "Invalid" in data["message"]
        
    def test_leave_sync_group(self):
        """Test leaving a sync group."""
        # Create and join sync group
        response = client.post("/api/sync/create", json={"description": "Leave Test"})
        assert response.status_code == 200
        
        # Leave the group
        response = client.post("/api/sync/leave")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify no longer synced
        response = client.get("/api/sync/status")
        data = response.json()
        assert data["synced"] is False

class TestResetAPI:
    """Test reset functionality."""
    
    def test_reset_all_data(self):
        """Test resetting all user data."""
        # Set some preferences first
        preferences = [
            {"key": "rating:course1", "value": "5", "type": "course_rating"},
            {"key": "played:video1", "value": "true", "type": "played"}
        ]
        
        for pref in preferences:
            response = client.post("/api/preferences", json=pref)
            assert response.status_code == 200
            
        # Create sync group
        response = client.post("/api/sync/create", json={"description": "Reset Test"})
        assert response.status_code == 200
        
        # Reset all data
        response = client.post("/api/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reset successfully" in data["message"]

class TestAPIErrorHandling:
    """Test API error handling scenarios."""
    
    @patch('app.main.get_db')
    def test_database_unavailable_preferences(self, mock_db):
        """Test preferences API when database is unavailable."""
        # Mock database to raise an exception
        mock_db.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/preferences")
        assert response.status_code == 503
        assert "Database temporarily unavailable" in response.json()["detail"]
        
    @patch('app.main.get_db')
    def test_database_unavailable_sync_create(self, mock_db):
        """Test sync creation when database is unavailable."""
        mock_db.side_effect = Exception("Database connection failed")
        
        response = client.post("/api/sync/create", json={"description": "Test"})
        assert response.status_code == 500
        
    def test_invalid_json_format(self):
        """Test handling of invalid JSON in requests."""
        response = client.post(
            "/api/preferences",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error
        
    def test_missing_content_type(self):
        """Test handling of missing content type."""
        response = client.post("/api/preferences", data='{"key": "test"}')
        # Should handle gracefully, exact behavior depends on FastAPI setup

class TestCrossDeviceSync:
    """Test cross-device synchronization scenarios."""
    
    def test_preferences_sync_between_devices(self):
        """Test that preferences sync between devices in same group."""
        # Device 1: Create sync group and set preference
        response = client.post("/api/sync/create", json={"description": "Cross Device Test"})
        sync_data = response.json()
        sync_code = sync_data["sync_code"]
        
        pref_data = {"key": "rating:sync_test", "value": "4", "type": "course_rating"}
        response = client.post("/api/preferences", json=pref_data)
        assert response.status_code == 200
        
        # Device 2: Join sync group and check preferences
        with TestClient(app) as client2:
            # Join the sync group
            join_data = {"sync_code": sync_code, "device_name": "Device 2"}
            response = client2.post("/api/sync/join", json=join_data)
            assert response.status_code == 200
            
            # Check if preferences are synced
            response = client2.get("/api/preferences")
            assert response.status_code == 200
            data = response.json()
            
            # Should see the preference from device 1
            assert "rating:sync_test" in data
            assert data["rating:sync_test"]["value"] == "4"
            assert data["rating:sync_test"]["synced_from"] is True
            
    def test_bidirectional_sync(self):
        """Test bidirectional synchronization between devices."""
        # Device 1: Create sync group
        response = client.post("/api/sync/create", json={"description": "Bidirectional Test"})
        sync_code = response.json()["sync_code"]
        
        # Device 2: Join sync group  
        with TestClient(app) as client2:
            join_data = {"sync_code": sync_code, "device_name": "Device 2"}
            response = client2.post("/api/sync/join", json=join_data)
            assert response.status_code == 200
            
            # Device 2: Set a preference
            pref_data = {"key": "rating:bidirectional", "value": "3", "type": "course_rating"}
            response = client2.post("/api/preferences", json=pref_data)
            assert response.status_code == 200
            
        # Device 1: Should see Device 2's preference
        response = client.get("/api/preferences")
        data = response.json()
        assert "rating:bidirectional" in data
        assert data["rating:bidirectional"]["value"] == "3"

class TestSpecialCharacters:
    """Test handling of special characters and edge cases."""
    
    def test_unicode_preference_values(self):
        """Test preferences with Unicode characters."""
        pref_data = {
            "key": "rating:unicode_test",
            "value": "🔥🔥🔥🔥🔥",
            "type": "course_rating"
        }
        
        response = client.post("/api/preferences", json=pref_data)
        assert response.status_code == 200
        
        response = client.get("/api/preferences")
        data = response.json()
        assert data["rating:unicode_test"]["value"] == "🔥🔥🔥🔥🔥"
        
    def test_sync_group_unicode_description(self):
        """Test sync group with Unicode description."""
        group_data = {"description": "🔥 Test Group with émojis 🚀"}
        
        response = client.post("/api/sync/create", json=group_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestRateLimiting:
    """Test rate limiting and abuse prevention (if implemented)."""
    
    def test_multiple_rapid_requests(self):
        """Test handling of multiple rapid requests."""
        # Make multiple rapid preference updates
        for i in range(50):
            pref_data = {
                "key": f"rating:rapid_test_{i}",
                "value": str(i % 5 + 1),
                "type": "course_rating"
            }
            response = client.post("/api/preferences", json=pref_data)
            # Should handle gracefully without errors
            assert response.status_code in [200, 429]  # 429 if rate limited
            
    def test_large_preference_batch(self):
        """Test handling of large batches of preferences."""
        # Set many preferences to test performance
        for i in range(100):
            pref_data = {
                "key": f"rating:batch_test_{i}",
                "value": str((i % 5) + 1),
                "type": "course_rating"
            }
            response = client.post("/api/preferences", json=pref_data)
            assert response.status_code == 200
            
        # Verify all were saved
        response = client.get("/api/preferences")
        assert response.status_code == 200
        data = response.json()
        batch_prefs = {k: v for k, v in data.items() if k.startswith("rating:batch_test_")}
        assert len(batch_prefs) == 100
