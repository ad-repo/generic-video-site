import os
import hashlib
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, ForeignKey, text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./db/user_preferences.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    user_agent = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    preference_key = Column(String, index=True)  # e.g., "progress:video1.mp4", "rating:Course1"
    preference_value = Column(Text)  # Store as string, parse as needed
    preference_type = Column(String)  # "progress", "played", "course_rating", "video_rating"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VideoSummary(Base):
    __tablename__ = "video_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_path = Column(Text, nullable=False, index=True)
    status = Column(String, default="pending", index=True)  # pending | processing | completed | failed | no_audio
    summary = Column(Text)
    transcript = Column(Text)
    model_used = Column(String, default="whisper-base+llama3.2:7b")
    audio_duration_seconds = Column(Float)
    processing_time_seconds = Column(Float)
    error_message = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('video_path', name='uq_video_summaries_video_path'),
        Index('ix_video_summaries_status_generated', 'status', 'generated_at'),
    )

class VideoSummaryVersion(Base):
    __tablename__ = "video_summary_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_path = Column(Text, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    summary = Column(Text)
    transcript = Column(Text)
    model_used = Column(String)
    processing_time_seconds = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('video_path', 'version', name='uq_video_summary_versions_path_ver'),
        Index('ix_video_summary_versions_path_time', 'video_path', 'generated_at'),
    )

def create_tables():
    """Create all database tables"""
    try:
        # Ensure the database directory exists
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        
        # Check if we can write to the database directory
        if db_dir and not os.access(db_dir, os.W_OK):
            print(f"⚠️ Warning: No write permission to database directory: {db_dir}")
            
        Base.metadata.create_all(bind=engine)
        # Lightweight SQLite migration: ensure new columns exist
        try:
            with engine.connect() as conn:
                # Add processing_time_seconds to video_summary_versions if missing
                res = conn.execute(text("PRAGMA table_info('video_summary_versions')")).fetchall()
                cols = {row[1] for row in res}
                if 'processing_time_seconds' not in cols:
                    conn.execute(text("ALTER TABLE video_summary_versions ADD COLUMN processing_time_seconds FLOAT"))
        except Exception as e:
            print(f"⚠️ Migration check failed (non-fatal): {e}")
        print(f"Database tables created at: {db_path}")
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection test successful")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print(f"Database URL: {DATABASE_URL}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Database path: {db_path}")
        if db_dir:
            print(f"Database directory exists: {os.path.exists(db_dir)}")
            print(f"Database directory writable: {os.access(db_dir, os.W_OK) if os.path.exists(db_dir) else 'N/A'}")
        raise

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_user_id(ip_address: str, user_agent: str) -> str:
    """Generate a consistent user ID based on IP and User-Agent"""
    # Normalize ALL Docker container IPs to prevent new user IDs on each deployment
    normalized_ip = ip_address
    
    # Check if this looks like a Docker container IP (single client connecting to container)
    # Docker can assign various private IP ranges: 172.x.x.x, 192.168.x.x, 10.x.x.x
    if (ip_address.startswith('172.') or 
        ip_address.startswith('192.168.') or 
        ip_address.startswith('10.')) and len(ip_address.split('.')) == 4:
        
        # Check if it's a Docker gateway IP (usually ends in .1)
        if ip_address.endswith('.1'):
            # This is likely a Docker container request - normalize to consistent IP
            normalized_ip = "172.docker.internal"
        else:
            # This might be a real local network IP - keep as is
            normalized_ip = ip_address
    
    # Create a hash that's consistent but not easily reversible
    combined = f"{normalized_ip}:{user_agent}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def get_or_create_user(db, ip_address: str, user_agent: str) -> User:
    """Get existing user or create new one"""
    user_id = generate_user_id(ip_address, user_agent)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update last seen
        user.last_seen = datetime.utcnow()
        db.commit()
    
    return user
