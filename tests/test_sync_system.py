import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, User, get_or_create_user
from app.sync_system import (
    SyncGroup, DeviceSync, create_sync_group, join_sync_group, 
    get_sync_group_users, get_device_info, generate_sync_code
)

@pytest.fixture
def test_db():
    """Create a temporary test database for sync tests."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite:///{db_path}"
    
    # Create engine and session
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    
    yield db
    
    # Cleanup
    db.close()
    os.close(db_fd)
    os.unlink(db_path)

class TestSyncCodeGeneration:
    """Test sync code generation functionality."""
    
    def test_generate_sync_code(self):
        """Test that sync codes are generated correctly."""
        code = generate_sync_code()
        
        # Should be 6 characters
        assert len(code) == 6
        
        # Should be uppercase
        assert code.isupper()
        
        # Should only contain allowed characters (no 0, O, 1, I)
        allowed_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        assert all(char in allowed_chars for char in code)
        
    def test_generate_unique_codes(self):
        """Test that generated codes are unique."""
        codes = [generate_sync_code() for _ in range(100)]
        
        # All codes should be unique (very high probability)
        assert len(set(codes)) == len(codes)

class TestSyncGroupCreation:
    """Test sync group creation functionality."""
    
    def test_create_sync_group_basic(self, test_db):
        """Test basic sync group creation."""
        # Create a user first
        user = get_or_create_user(test_db, "192.168.1.100", "Test Browser")
        
        # Create sync group
        sync_code = create_sync_group(test_db, user.id, "Test Group")
        
        # Verify sync group was created
        sync_group = test_db.query(SyncGroup).filter(
            SyncGroup.sync_code == sync_code
        ).first()
        
        assert sync_group is not None
        assert sync_group.master_user_id == user.id
        assert sync_group.description == "Test Group"
        assert sync_group.expires_at is None  # Permanent sync groups
        assert sync_group.created_at is not None
        
        # Verify device sync was created for master
        device_sync = test_db.query(DeviceSync).filter(
            DeviceSync.sync_code == sync_code
        ).first()
        
        assert device_sync is not None
        assert device_sync.device_user_id == user.id
        assert device_sync.sync_code == sync_code

    def test_create_sync_group_no_description(self, test_db):
        """Test creating sync group without description."""
        user = get_or_create_user(test_db, "192.168.1.101", "Test Browser 2")
        
        sync_code = create_sync_group(test_db, user.id)
        
        sync_group = test_db.query(SyncGroup).filter(
            SyncGroup.sync_code == sync_code
        ).first()
        
        assert sync_group is not None
        assert sync_group.description is None

    def test_create_multiple_sync_groups(self, test_db):
        """Test creating multiple sync groups."""
        user1 = get_or_create_user(test_db, "192.168.1.102", "Browser 1")
        user2 = get_or_create_user(test_db, "192.168.1.103", "Browser 2")
        
        code1 = create_sync_group(test_db, user1.id, "Group 1")
        code2 = create_sync_group(test_db, user2.id, "Group 2")
        
        # Codes should be different
        assert code1 != code2
        
        # Both groups should exist
        groups = test_db.query(SyncGroup).all()
        assert len(groups) == 2
        
        group_codes = {group.sync_code for group in groups}
        assert group_codes == {code1, code2}

class TestSyncGroupJoining:
    """Test joining sync groups functionality."""
    
    def test_join_sync_group_success(self, test_db):
        """Test successfully joining a sync group."""
        # Create master user and sync group
        master_user = get_or_create_user(test_db, "192.168.1.200", "Master Browser")
        sync_code = create_sync_group(test_db, master_user.id, "Master Group")
        
        # Create second user
        second_user = get_or_create_user(test_db, "192.168.1.201", "Second Browser")
        
        # Join sync group
        result = join_sync_group(test_db, sync_code, second_user.id, "Second Device")
        assert result is True
        
        # Verify device sync was created
        device_syncs = test_db.query(DeviceSync).filter(
            DeviceSync.sync_code == sync_code
        ).all()
        
        assert len(device_syncs) == 2  # Master + second user
        
        second_device = test_db.query(DeviceSync).filter(
            DeviceSync.device_user_id == second_user.id
        ).first()
        
        assert second_device is not None
        assert second_device.sync_code == sync_code
        assert second_device.device_name == "Second Device"

    def test_join_nonexistent_group(self, test_db):
        """Test joining a non-existent sync group."""
        user = get_or_create_user(test_db, "192.168.1.202", "Test Browser")
        
        result = join_sync_group(test_db, "INVALID", user.id, "Device")
        assert result is False

    def test_join_group_twice(self, test_db):
        """Test joining the same group twice with same user."""
        # Create master and group
        master = get_or_create_user(test_db, "192.168.1.203", "Master")
        sync_code = create_sync_group(test_db, master.id)
        
        # Create user and join
        user = get_or_create_user(test_db, "192.168.1.204", "Joiner")
        
        result1 = join_sync_group(test_db, sync_code, user.id, "Device 1")
        assert result1 is True
        
        # Join again with same user
        result2 = join_sync_group(test_db, sync_code, user.id, "Device 2")
        assert result2 is True  # Should update last_sync
        
        # Should still only have one device sync for this user
        user_syncs = test_db.query(DeviceSync).filter(
            DeviceSync.device_user_id == user.id
        ).all()
        assert len(user_syncs) == 1

    def test_case_insensitive_join(self, test_db):
        """Test that sync code joining is case insensitive."""
        master = get_or_create_user(test_db, "192.168.1.205", "Master")
        sync_code = create_sync_group(test_db, master.id)
        
        user = get_or_create_user(test_db, "192.168.1.206", "Joiner")
        
        # Try joining with lowercase code
        result = join_sync_group(test_db, sync_code.lower(), user.id, "Device")
        assert result is True

class TestDeviceInfo:
    """Test device information extraction."""
    
    def test_iphone_detection(self):
        """Test iPhone user agent detection."""
        iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"
        device_info = get_device_info(iphone_ua)
        assert device_info == "iPhone Safari"
        
    def test_android_detection(self):
        """Test Android user agent detection."""
        android_ua = "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 Chrome/91.0.4472.120"
        device_info = get_device_info(android_ua)
        assert device_info == "Android Chrome"
        
    def test_desktop_chrome_detection(self):
        """Test desktop Chrome detection."""
        chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124"
        device_info = get_device_info(chrome_ua)
        assert device_info == "Desktop Chrome"
        
    def test_desktop_safari_detection(self):
        """Test desktop Safari detection."""
        safari_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/604.1"
        device_info = get_device_info(safari_ua)
        assert device_info == "Desktop Safari"
        
    def test_firefox_detection(self):
        """Test Firefox detection."""
        firefox_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        device_info = get_device_info(firefox_ua)
        assert device_info == "Desktop Firefox"
        
    def test_unknown_browser(self):
        """Test unknown browser fallback."""
        unknown_ua = "SomeUnknownBrowser/1.0"
        device_info = get_device_info(unknown_ua)
        assert device_info == "Unknown Device"

class TestSyncGroupUsers:
    """Test getting sync group users functionality."""
    
    def test_get_sync_group_users_single(self, test_db):
        """Test getting users when user is not in any sync group."""
        user = get_or_create_user(test_db, "192.168.1.300", "Solo User")
        
        users = get_sync_group_users(test_db, user.id)
        assert users == [user.id]  # Should return just the user
        
    def test_get_sync_group_users_multiple(self, test_db):
        """Test getting users from a sync group with multiple members."""
        # Create users
        master = get_or_create_user(test_db, "192.168.1.301", "Master")
        user1 = get_or_create_user(test_db, "192.168.1.302", "User 1")
        user2 = get_or_create_user(test_db, "192.168.1.303", "User 2")
        
        # Create sync group and add users
        sync_code = create_sync_group(test_db, master.id, "Multi User Group")
        join_sync_group(test_db, sync_code, user1.id, "Device 1")
        join_sync_group(test_db, sync_code, user2.id, "Device 2")
        
        # Get sync group users for any member
        users_from_master = set(get_sync_group_users(test_db, master.id))
        users_from_user1 = set(get_sync_group_users(test_db, user1.id))
        users_from_user2 = set(get_sync_group_users(test_db, user2.id))
        
        expected_users = {master.id, user1.id, user2.id}
        
        assert users_from_master == expected_users
        assert users_from_user1 == expected_users
        assert users_from_user2 == expected_users

class TestSyncGroupPermanence:
    """Test that sync groups are permanent (no expiration)."""
    
    def test_sync_group_no_expiration(self, test_db):
        """Test that created sync groups have no expiration."""
        user = get_or_create_user(test_db, "192.168.1.400", "Permanent User")
        sync_code = create_sync_group(test_db, user.id, "Permanent Group")
        
        sync_group = test_db.query(SyncGroup).filter(
            SyncGroup.sync_code == sync_code
        ).first()
        
        assert sync_group.expires_at is None
        
    def test_join_permanent_group(self, test_db):
        """Test joining a permanent sync group."""
        master = get_or_create_user(test_db, "192.168.1.401", "Master")
        sync_code = create_sync_group(test_db, master.id)
        
        # Set expires_at to None explicitly (should already be None)
        sync_group = test_db.query(SyncGroup).filter(
            SyncGroup.sync_code == sync_code
        ).first()
        sync_group.expires_at = None
        test_db.commit()
        
        # Join should still work
        user = get_or_create_user(test_db, "192.168.1.402", "Joiner")
        result = join_sync_group(test_db, sync_code, user.id, "Device")
        
        assert result is True

class TestSyncGroupEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_sync_code(self, test_db):
        """Test behavior with empty sync code."""
        user = get_or_create_user(test_db, "192.168.1.500", "Test User")
        
        result = join_sync_group(test_db, "", user.id, "Device")
        assert result is False
        
    def test_none_sync_code(self, test_db):
        """Test behavior with None sync code."""
        user = get_or_create_user(test_db, "192.168.1.501", "Test User")
        
        with pytest.raises(Exception):  # Should raise an error
            join_sync_group(test_db, None, user.id, "Device")
            
    def test_very_long_device_name(self, test_db):
        """Test behavior with very long device name."""
        master = get_or_create_user(test_db, "192.168.1.502", "Master")
        sync_code = create_sync_group(test_db, master.id)
        
        user = get_or_create_user(test_db, "192.168.1.503", "User")
        
        long_name = "x" * 1000  # Very long device name
        result = join_sync_group(test_db, sync_code, user.id, long_name)
        
        # Should either succeed or fail gracefully
        assert isinstance(result, bool)
        
    def test_special_characters_in_description(self, test_db):
        """Test sync group with special characters in description."""
        user = get_or_create_user(test_db, "192.168.1.504", "Special User")
        
        special_desc = "🔥 Test Group with émojis & spéçiál chârs! @#$%"
        sync_code = create_sync_group(test_db, user.id, special_desc)
        
        sync_group = test_db.query(SyncGroup).filter(
            SyncGroup.sync_code == sync_code
        ).first()
        
        assert sync_group is not None
        assert sync_group.description == special_desc
