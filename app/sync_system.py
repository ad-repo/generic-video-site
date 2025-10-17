"""
Cross-device sync system using shareable sync codes
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Text
from .database import Base, get_db
from sqlalchemy.orm import Session

class SyncGroup(Base):
    __tablename__ = "sync_groups"
    
    sync_code = Column(String, primary_key=True)  # 6-digit code like "ABC123"
    master_user_id = Column(String)  # Original user who created the sync group
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration (null = never expires)
    description = Column(Text, nullable=True)  # Optional description like "John's devices"

class DeviceSync(Base):
    __tablename__ = "device_syncs"
    
    id = Column(String, primary_key=True)  # Auto-generated UUID
    sync_code = Column(String, index=True)  # Links to SyncGroup
    device_user_id = Column(String, index=True)  # Original device-specific user ID
    device_name = Column(String)  # e.g. "iPhone Safari", "Desktop Chrome"
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_sync = Column(DateTime, default=datetime.utcnow)

def generate_sync_code() -> str:
    """Generate a 6-character sync code like ABC123"""
    # Use uppercase letters and numbers, avoid confusing characters
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(chars) for _ in range(6))

def create_sync_group(db: Session, master_user_id: str, description: str = None) -> str:
    """Create a new sync group and return the sync code"""
    
    # Generate a unique sync code
    for _ in range(10):  # Try up to 10 times to avoid collisions
        sync_code = generate_sync_code()
        existing = db.query(SyncGroup).filter(SyncGroup.sync_code == sync_code).first()
        if not existing:
            break
    else:
        raise Exception("Failed to generate unique sync code")
    
    # Create sync group (permanent - no expiration)
    sync_group = SyncGroup(
        sync_code=sync_code,
        master_user_id=master_user_id,
        expires_at=None,  # Never expires
        description=description
    )
    db.add(sync_group)
    
    # Add the master device to the sync group
    device_sync = DeviceSync(
        id=f"device_{secrets.token_hex(8)}",
        sync_code=sync_code,
        device_user_id=master_user_id,
        device_name="Master Device"
    )
    db.add(device_sync)
    
    db.commit()
    return sync_code

def join_sync_group(db: Session, sync_code: str, device_user_id: str, device_name: str) -> bool:
    """Join an existing sync group with a sync code"""
    
    # Find the sync group (no expiration check since groups are permanent)
    sync_group = db.query(SyncGroup).filter(
        SyncGroup.sync_code == sync_code.upper()
    ).first()
    
    if not sync_group:
        return False  # Sync code not found or expired
    
    # Check if device is already in sync group
    existing = db.query(DeviceSync).filter(
        DeviceSync.sync_code == sync_code.upper(),
        DeviceSync.device_user_id == device_user_id
    ).first()
    
    if existing:
        # Update last sync time
        existing.last_sync = datetime.utcnow()
        existing.device_name = device_name
    else:
        # Add new device to sync group
        device_sync = DeviceSync(
            id=f"device_{secrets.token_hex(8)}",
            sync_code=sync_code.upper(),
            device_user_id=device_user_id,
            device_name=device_name
        )
        db.add(device_sync)
    
    db.commit()
    return True

def get_sync_group_users(db: Session, user_id: str) -> list:
    """Get all user IDs in the same sync group as the given user"""
    
    # Find which sync group this user belongs to
    device_sync = db.query(DeviceSync).filter(
        DeviceSync.device_user_id == user_id
    ).first()
    
    if not device_sync:
        return [user_id]  # User not in any sync group, return just themselves
    
    # Get all devices in the same sync group
    all_devices = db.query(DeviceSync).filter(
        DeviceSync.sync_code == device_sync.sync_code
    ).all()
    
    return [device.device_user_id for device in all_devices]

# cleanup_expired_sync_groups function removed - sync groups are now permanent

def get_device_info(user_agent: str) -> str:
    """Extract readable device info from user agent"""
    
    user_agent = user_agent.lower()
    
    # Detect mobile devices
    if 'iphone' in user_agent:
        if 'safari' in user_agent and 'chrome' not in user_agent:
            return "iPhone Safari"
        elif 'chrome' in user_agent:
            return "iPhone Chrome"
        else:
            return "iPhone"
    elif 'ipad' in user_agent:
        return "iPad"
    elif 'android' in user_agent:
        if 'chrome' in user_agent:
            return "Android Chrome"
        else:
            return "Android"
    
    # Detect desktop browsers
    elif 'chrome' in user_agent and 'edge' not in user_agent:
        return "Desktop Chrome"
    elif 'firefox' in user_agent:
        return "Desktop Firefox"
    elif 'safari' in user_agent:
        return "Desktop Safari"
    elif 'edge' in user_agent:
        return "Desktop Edge"
    
    return "Unknown Device"
