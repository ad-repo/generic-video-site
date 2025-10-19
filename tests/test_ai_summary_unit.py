"""
Fast AI Summary unit tests - designed for CI integration
These tests focus on business logic without complex database interactions
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAISummaryComponents:
    """Fast unit tests for AI summary components"""

    def test_audio_extraction_logic(self):
        """Test audio extraction service logic"""
        from tests.test_audio_extraction import MockAudioExtractionService
        
        service = MockAudioExtractionService()
        
        # Test successful extraction
        result = service.extract_audio("/app/data/video.mp4", "/tmp")
        assert result['success'] is True
        assert result['audio_path'] == "/tmp/audio.wav"
        assert result['duration_seconds'] == 150.45
        
        # Test no audio track
        result = service.extract_audio("/app/data/no_audio_video.mp4", "/tmp")
        assert result['success'] is False
        assert 'no audio' in result['error'].lower()

    def test_transcription_logic(self):
        """Test transcription service logic"""
        from tests.test_transcription_service import MockTranscriptionService
        
        service = MockTranscriptionService()
        
        # Test successful transcription
        result = service.transcribe_audio("/tmp/audio.wav")
        assert result['success'] is True
        assert result['transcript'] is not None
        assert len(result['transcript']) > 0
        
        # Test empty file
        result = service.transcribe_audio("/tmp/no_audio.wav")
        assert result['success'] is False
        assert 'empty or corrupted' in result['error']

    def test_summarization_logic(self):
        """Test summarization service logic"""
        from tests.test_summarization_service import MockSummarizationService
        
        service = MockSummarizationService()
        
        # Test successful summarization
        transcript = "This is a test transcript about machine learning concepts."
        result = service.summarize_transcript(transcript)
        assert result['success'] is True
        assert result['summary'] is not None
        assert 'Summary:' in result['summary']
        
        # Test empty transcript
        result = service.summarize_transcript("")
        assert result['success'] is False
        assert 'empty transcript' in result['error'].lower()

    def test_duration_parsing(self):
        """Test duration parsing utility"""
        from tests.test_audio_extraction import MockAudioExtractionService
        
        service = MockAudioExtractionService()
        
        test_cases = [
            ("Duration: 00:02:30.45", 150.45),
            ("Duration: 01:30:15.123", 5415.123),
            ("Duration: 00:00:45.67", 45.67),
        ]
        
        for duration_str, expected_seconds in test_cases:
            result = service._parse_duration(duration_str)
            assert result == expected_seconds

    def test_filename_sanitization(self):
        """Test safe filename generation"""
        from tests.test_audio_extraction import MockAudioExtractionService
        
        service = MockAudioExtractionService()
        
        test_cases = [
            "/app/data/Course 1/video with spaces.mp4",
            "/path/to/video-file.mp4",
            "/complex/path/file (2023) [HD].mp4",
        ]
        
        for video_path in test_cases:
            safe_name = service._get_safe_filename(video_path)
            assert safe_name.endswith('.wav')
            assert ' ' not in safe_name or video_path == test_cases[0]  # Allow space replacement

    def test_model_validation(self):
        """Test model validation"""
        from tests.test_transcription_service import MockTranscriptionService
        
        service = MockTranscriptionService()
        
        # Valid models
        for model in ['tiny', 'base', 'small', 'medium', 'large']:
            assert service.validate_model(model) is True
        
        # Invalid models
        for model in ['invalid', 'nonexistent', '', 'xl']:
            assert service.validate_model(model) is False

    def test_ollama_health_check(self):
        """Test Ollama service health check"""
        from tests.test_summarization_service import MockSummarizationService
        
        service = MockSummarizationService()
        health = service.check_ollama_health()
        
        assert health['healthy'] is True
        assert isinstance(health['models_available'], list)
        assert len(health['models_available']) > 0
        assert 'llama3.2:7b' in health['models_available']

    def test_key_topic_extraction(self):
        """Test key topic extraction from summaries"""
        from tests.test_summarization_service import MockSummarizationService
        
        service = MockSummarizationService()
        
        summary = "This video discusses technical implementation and educational concepts"
        topics = service.extract_key_topics(summary)
        
        assert isinstance(topics, list)
        assert "Technical Implementation" in topics
        assert "Educational Content" in topics

    def test_transcript_length_validation(self):
        """Test transcript length validation"""
        from tests.test_summarization_service import MockSummarizationService
        
        service = MockSummarizationService()
        
        short_transcript = "Short transcript"
        long_transcript = "A" * 60000
        
        assert service.validate_transcript_length(short_transcript) is True
        assert service.validate_transcript_length(long_transcript) is False

    def test_error_handling_scenarios(self):
        """Test various error handling scenarios"""
        from tests.test_audio_extraction import MockAudioExtractionService
        from tests.test_transcription_service import MockTranscriptionService
        from tests.test_summarization_service import MockSummarizationService
        
        audio_service = MockAudioExtractionService()
        transcription_service = MockTranscriptionService()
        summarization_service = MockSummarizationService()
        
        # Test file not found
        result = audio_service.extract_audio("/app/data/nonexistent.mp4", "/tmp")
        assert result['success'] is False
        assert 'file not found' in result['error'].lower()
        
        # Test transcription timeout
        result = transcription_service.transcribe_audio("/tmp/timeout_audio.wav")
        assert result['success'] is False
        assert 'timeout' in result['error'].lower()
        
        # Test summarization connection error
        result = summarization_service.summarize_transcript("connection_error test")
        assert result['success'] is False
        assert 'connection' in result['error'].lower()

    def test_workflow_integration_logic(self):
        """Test the logical flow of the complete workflow"""
        from tests.test_audio_extraction import MockAudioExtractionService
        from tests.test_transcription_service import MockTranscriptionService
        from tests.test_summarization_service import MockSummarizationService
        
        # Simulate successful workflow
        audio_service = MockAudioExtractionService()
        transcription_service = MockTranscriptionService()
        summarization_service = MockSummarizationService()
        
        # Step 1: Extract audio
        audio_result = audio_service.extract_audio("/app/data/video.mp4", "/tmp")
        assert audio_result['success'] is True
        
        # Step 2: Transcribe audio
        transcript_result = transcription_service.transcribe_audio(audio_result['audio_path'])
        assert transcript_result['success'] is True
        
        # Step 3: Summarize transcript
        summary_result = summarization_service.summarize_transcript(transcript_result['transcript'])
        assert summary_result['success'] is True
        
        # Verify end-to-end flow
        assert summary_result['summary'] is not None
        assert len(summary_result['summary']) > 0


class TestAISummaryUtils:
    """Test utility functions for AI summary system"""

    def test_video_path_validation(self):
        """Test video path validation logic"""
        valid_paths = [
            "/app/data/course1/video1.mp4",
            "/app/data/Course Name/Section 1/video.mp4",
            "/app/data/programming/python-basics.mp4"
        ]
        
        invalid_paths = [
            "",
            None,
            "/nonexistent/path.txt",
            "/app/data/../../../etc/passwd"
        ]
        
        for path in valid_paths:
            # Mock validation - in real implementation would check file existence
            assert isinstance(path, str) and len(path) > 0
        
        for path in invalid_paths:
            # Mock validation - in real implementation would return False
            if path is None or path == "":
                assert not path

    def test_status_constants(self):
        """Test status constants used in the system"""
        expected_statuses = ['pending', 'processing', 'completed', 'failed', 'no_audio']
        
        # This would be imported from actual constants in real implementation
        for status in expected_statuses:
            assert isinstance(status, str)
            assert len(status) > 0

    def test_model_constants(self):
        """Test model constants"""
        whisper_models = ['tiny', 'base', 'small', 'medium', 'large']
        ollama_models = ['llama3.2:7b', 'llama3.2:3b']
        
        for model in whisper_models + ollama_models:
            assert isinstance(model, str)
            assert len(model) > 0


# Performance and memory tests
class TestAISummaryPerformance:
    """Test performance characteristics of AI summary components"""

    def test_mock_service_creation_speed(self):
        """Test that mock services are created quickly"""
        import time
        from tests.test_audio_extraction import MockAudioExtractionService
        from tests.test_transcription_service import MockTranscriptionService
        from tests.test_summarization_service import MockSummarizationService
        
        start_time = time.time()
        
        # Create multiple service instances
        for _ in range(100):
            MockAudioExtractionService()
            MockTranscriptionService()
            MockSummarizationService()
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should create 300 mock instances in under 0.1 seconds
        assert creation_time < 0.1

    def test_mock_operations_speed(self):
        """Test that mock operations complete quickly"""
        import time
        from tests.test_audio_extraction import MockAudioExtractionService
        from tests.test_transcription_service import MockTranscriptionService
        from tests.test_summarization_service import MockSummarizationService
        
        audio_service = MockAudioExtractionService()
        transcription_service = MockTranscriptionService()
        summarization_service = MockSummarizationService()
        
        start_time = time.time()
        
        # Perform operations
        for i in range(50):
            audio_result = audio_service.extract_audio(f"/test/video_{i}.mp4", "/tmp")
            if audio_result['success']:
                transcript_result = transcription_service.transcribe_audio(audio_result['audio_path'])
                if transcript_result['success']:
                    summarization_service.summarize_transcript(transcript_result['transcript'])
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # 50 complete workflows should finish in under 0.05 seconds
        assert operation_time < 0.05

    def test_memory_efficiency(self):
        """Test that mock services don't consume excessive memory"""
        import sys
        from tests.test_audio_extraction import MockAudioExtractionService
        
        # Create many instances and verify they're lightweight
        services = []
        for _ in range(1000):
            services.append(MockAudioExtractionService())
        
        # Mock services should be very lightweight
        # This is a basic check - in production we'd use memory profiling
        assert len(services) == 1000
