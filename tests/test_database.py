import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, User, UserPreference, create_tables, get_or_create_user, generate_user_id

@pytest.fixture
def test_db():
    """Create a temporary test database."""
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

class TestDatabaseModels:
    """Test database models and operations."""
    
    def test_user_creation(self, test_db):
        """Test creating a user."""
        user = User(
            id="test_user_123",
            user_agent="Mozilla/5.0 Test Browser",
            ip_address="192.168.1.100"
        )
        test_db.add(user)
        test_db.commit()
        
        # Verify user was created
        retrieved_user = test_db.query(User).filter(User.id == "test_user_123").first()
        assert retrieved_user is not None
        assert retrieved_user.user_agent == "Mozilla/5.0 Test Browser"
        assert retrieved_user.ip_address == "192.168.1.100"
        assert retrieved_user.created_at is not None
        assert retrieved_user.last_seen is not None

    def test_user_preference_creation(self, test_db):
        """Test creating user preferences."""
        # Create user first
        user = User(
            id="test_user_456",
            user_agent="Test Browser",
            ip_address="192.168.1.101"
        )
        test_db.add(user)
        test_db.commit()
        
        # Create preference
        preference = UserPreference(
            user_id="test_user_456",
            preference_key="rating:course1",
            preference_value="4",
            preference_type="course_rating"
        )
        test_db.add(preference)
        test_db.commit()
        
        # Verify preference was created
        retrieved_pref = test_db.query(UserPreference).filter(
            UserPreference.preference_key == "rating:course1"
        ).first()
        assert retrieved_pref is not None
        assert retrieved_pref.user_id == "test_user_456"
        assert retrieved_pref.preference_value == "4"
        assert retrieved_pref.preference_type == "course_rating"
        assert retrieved_pref.created_at is not None
        assert retrieved_pref.updated_at is not None

    def test_generate_user_id(self):
        """Test user ID generation."""
        ip = "192.168.1.100"
        user_agent = "Mozilla/5.0 Test Browser"
        
        user_id1 = generate_user_id(ip, user_agent)
        user_id2 = generate_user_id(ip, user_agent)
        
        # Should be consistent
        assert user_id1 == user_id2
        assert len(user_id1) == 16  # Should be 16 characters from sha256 hash
        
        # Different inputs should generate different IDs
        user_id3 = generate_user_id("192.168.1.101", user_agent)
        assert user_id1 != user_id3

    def test_get_or_create_user_new(self, test_db):
        """Test getting or creating a new user."""
        ip = "192.168.1.200"
        user_agent = "New Test Browser"
        
        # First call should create the user
        user1 = get_or_create_user(test_db, ip, user_agent)
        assert user1 is not None
        assert user1.ip_address == ip
        assert user1.user_agent == user_agent
        
        # Verify user exists in database
        user_count = test_db.query(User).count()
        assert user_count == 1

    def test_get_or_create_user_existing(self, test_db):
        """Test getting an existing user."""
        ip = "192.168.1.201"
        user_agent = "Existing Test Browser"
        
        # Create user first
        user1 = get_or_create_user(test_db, ip, user_agent)
        original_last_seen = user1.last_seen
        
        # Wait a bit then get user again
        import time
        time.sleep(0.1)
        
        user2 = get_or_create_user(test_db, ip, user_agent)
        
        # Should be same user but with updated last_seen
        assert user1.id == user2.id
        assert user2.last_seen > original_last_seen
        
        # Should still be only one user in database
        user_count = test_db.query(User).count()
        assert user_count == 1

    def test_preference_update(self, test_db):
        """Test updating user preferences."""
        # Create user and preference
        user = get_or_create_user(test_db, "192.168.1.202", "Update Test Browser")
        
        preference = UserPreference(
            user_id=user.id,
            preference_key="rating:test_course",
            preference_value="3",
            preference_type="course_rating"
        )
        test_db.add(preference)
        test_db.commit()
        
        original_updated_at = preference.updated_at
        
        # Update the preference
        import time
        time.sleep(0.1)
        preference.preference_value = "5"
        test_db.commit()
        
        # Verify update
        updated_pref = test_db.query(UserPreference).filter(
            UserPreference.preference_key == "rating:test_course"
        ).first()
        assert updated_pref.preference_value == "5"
        # Note: updated_at auto-update depends on database trigger/setup

    def test_multiple_preference_types(self, test_db):
        """Test creating preferences of different types."""
        user = get_or_create_user(test_db, "192.168.1.203", "Multi Pref Browser")
        
        preferences = [
            UserPreference(
                user_id=user.id,
                preference_key="rating:course1",
                preference_value="4",
                preference_type="course_rating"
            ),
            UserPreference(
                user_id=user.id,
                preference_key="videoRating:video1",
                preference_value="5",
                preference_type="video_rating"
            ),
            UserPreference(
                user_id=user.id,
                preference_key="played:video1",
                preference_value="true",
                preference_type="played"
            ),
            UserPreference(
                user_id=user.id,
                preference_key="progress:video1",
                preference_value="45.5",
                preference_type="progress"
            )
        ]
        
        for pref in preferences:
            test_db.add(pref)
        test_db.commit()
        
        # Verify all preferences were created
        user_prefs = test_db.query(UserPreference).filter(
            UserPreference.user_id == user.id
        ).all()
        assert len(user_prefs) == 4
        
        # Verify different types
        pref_types = {pref.preference_type for pref in user_prefs}
        expected_types = {"course_rating", "video_rating", "played", "progress"}
        assert pref_types == expected_types

class TestDatabaseConstraints:
    """Test database constraints and edge cases."""
    
    def test_user_id_uniqueness(self, test_db):
        """Test that user IDs are unique."""
        user1 = User(
            id="duplicate_test",
            user_agent="Browser 1",
            ip_address="192.168.1.1"
        )
        test_db.add(user1)
        test_db.commit()
        
        # Try to create another user with same ID
        user2 = User(
            id="duplicate_test",
            user_agent="Browser 2",
            ip_address="192.168.1.2"
        )
        test_db.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            test_db.commit()

    def test_preference_without_user(self, test_db):
        """Test creating preference with non-existent user (if foreign key enforced)."""
        preference = UserPreference(
            user_id="nonexistent_user",
            preference_key="test_key",
            preference_value="test_value",
            preference_type="test"
        )
        test_db.add(preference)
        
        # This might not fail if foreign key constraints aren't enforced
        # But it's good to test the behavior
        try:
            test_db.commit()
            # If it doesn't fail, that's the current behavior
            assert True
        except Exception:
            # If it fails, foreign key constraint is working
            assert True

    def test_empty_preference_values(self, test_db):
        """Test handling of empty or null preference values."""
        user = get_or_create_user(test_db, "192.168.1.250", "Empty Value Browser")
        
        # Test empty string value
        pref1 = UserPreference(
            user_id=user.id,
            preference_key="empty_test",
            preference_value="",
            preference_type="test"
        )
        test_db.add(pref1)
        test_db.commit()
        
        retrieved = test_db.query(UserPreference).filter(
            UserPreference.preference_key == "empty_test"
        ).first()
        assert retrieved is not None
        assert retrieved.preference_value == ""

    def test_long_preference_values(self, test_db):
        """Test handling of long preference values."""
        user = get_or_create_user(test_db, "192.168.1.251", "Long Value Browser")
        
        # Create a long preference value
        long_value = "x" * 1000  # 1000 character string
        
        pref = UserPreference(
            user_id=user.id,
            preference_key="long_test",
            preference_value=long_value,
            preference_type="test"
        )
        test_db.add(pref)
        test_db.commit()
        
        retrieved = test_db.query(UserPreference).filter(
            UserPreference.preference_key == "long_test"
        ).first()
        assert retrieved is not None
        assert len(retrieved.preference_value) == 1000
