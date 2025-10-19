"""
Test VideoSummary database model with proper isolation
"""
import pytest
import uuid
from datetime import datetime
from app.database import VideoSummary


class TestVideoSummaryModel:
    """Test VideoSummary database model operations"""

    def test_video_summary_creation(self, test_db):
        """Test creating a video summary"""
        unique_path = f"/test/video_{uuid.uuid4().hex[:8]}.mp4"
        
        video_summary = VideoSummary(
            video_path=unique_path,
            summary="This is a test summary",
            status="completed"
        )
        test_db.add(video_summary)
        test_db.commit()
        
        assert video_summary.id is not None
        assert video_summary.video_path == unique_path
        assert video_summary.summary == "This is a test summary"
        assert video_summary.status == "completed"
        assert video_summary.generated_at is not None

    def test_video_summary_unique_path_constraint(self, test_db):
        """Test that video_path must be unique"""
        unique_path = f"/test/duplicate_{uuid.uuid4().hex[:8]}.mp4"
        
        # Create first summary
        summary1 = VideoSummary(
            video_path=unique_path,
            summary="First summary",
            status="completed"
        )
        test_db.add(summary1)
        test_db.commit()
        
        # Try to create second summary with same path
        summary2 = VideoSummary(
            video_path=unique_path,
            summary="Second summary",
            status="completed"
        )
        test_db.add(summary2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

    def test_video_summary_status_values(self, test_db):
        """Test different status values"""
        statuses = ['pending', 'processing', 'completed', 'failed', 'no_audio']
        
        for i, status in enumerate(statuses):
            unique_path = f"/test/status_{i}_{uuid.uuid4().hex[:8]}.mp4"
            summary = VideoSummary(
                video_path=unique_path,
                status=status
            )
            test_db.add(summary)
        
        test_db.commit()
        
        # Verify all summaries were created
        summaries = test_db.query(VideoSummary).filter(
            VideoSummary.video_path.like('/test/status_%')
        ).all()
        assert len(summaries) == len(statuses)

    def test_video_summary_error_handling(self, test_db):
        """Test error message storage"""
        unique_path = f"/test/error_{uuid.uuid4().hex[:8]}.mp4"
        
        video_summary = VideoSummary(
            video_path=unique_path,
            status="failed",
            error_message="No audio track found in video file"
        )
        test_db.add(video_summary)
        test_db.commit()
        
        assert video_summary.status == "failed"
        assert video_summary.error_message == "No audio track found in video file"

    def test_video_summary_default_values(self, test_db):
        """Test default values for optional fields"""
        unique_path = f"/test/defaults_{uuid.uuid4().hex[:8]}.mp4"
        
        video_summary = VideoSummary(
            video_path=unique_path
        )
        test_db.add(video_summary)
        test_db.commit()
        
        assert video_summary.status == "pending"  # Default status
        assert video_summary.model_used == "whisper-base+llama3.2:7b"  # Default model
        assert video_summary.generated_at is not None
        assert video_summary.summary is None
        assert video_summary.transcript is None

    def test_video_summary_search_by_path(self, test_db):
        """Test searching summaries by video path"""
        base_path = f"/course1/section1_{uuid.uuid4().hex[:8]}"
        
        # Create multiple summaries
        paths = [
            f"{base_path}/video1.mp4",
            f"{base_path}/video2.mp4",
            f"/course2/section1/video1.mp4"
        ]
        
        for path in paths:
            summary = VideoSummary(
                video_path=path,
                summary=f"Summary for {path}",
                status="completed"
            )
            test_db.add(summary)
        
        test_db.commit()
        
        # Search for course1 summaries
        course1_summaries = test_db.query(VideoSummary).filter(
            VideoSummary.video_path.like(f'{base_path}%')
        ).all()
        
        assert len(course1_summaries) == 2
        
        # Search for specific video
        specific_summary = test_db.query(VideoSummary).filter(
            VideoSummary.video_path == f"{base_path}/video1.mp4"
        ).first()
        
        assert specific_summary is not None
        assert specific_summary.summary == f"Summary for {base_path}/video1.mp4"

    def test_video_summary_performance_metrics(self, test_db):
        """Test performance tracking fields"""
        unique_path = f"/test/performance_{uuid.uuid4().hex[:8]}.mp4"
        
        video_summary = VideoSummary(
            video_path=unique_path,
            status="completed",
            processing_time_seconds=125.5,
            audio_duration_seconds=300.0
        )
        test_db.add(video_summary)
        test_db.commit()
        
        assert video_summary.processing_time_seconds == 125.5
        assert video_summary.audio_duration_seconds == 300.0

    def test_video_summary_model_tracking(self, test_db):
        """Test model version tracking"""
        unique_path = f"/test/model_{uuid.uuid4().hex[:8]}.mp4"
        
        video_summary = VideoSummary(
            video_path=unique_path,
            status="completed",
            model_used="whisper-large+llama3.2:13b"
        )
        test_db.add(video_summary)
        test_db.commit()
        
        assert video_summary.model_used == "whisper-large+llama3.2:13b"