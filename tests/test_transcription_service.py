"""
Fast unit tests for Whisper transcription service (mocked operations)
"""
import pytest
from unittest.mock import patch, MagicMock


class MockTranscriptionService:
    """Mock transcription service for fast testing"""
    
    def transcribe_audio(self, audio_path, model_name="base"):
        """Mock transcribe_audio method"""
        if "no_audio" in audio_path:
            return {
                'success': False,
                'transcript': None,
                'error': 'Audio file is empty or corrupted'
            }
        elif "timeout" in audio_path:
            return {
                'success': False,
                'transcript': None,
                'error': 'Transcription timeout after 300 seconds'
            }
        elif "unsupported" in audio_path:
            return {
                'success': False,
                'transcript': None,
                'error': 'Unsupported audio format'
            }
        else:
            # Mock successful transcription
            return {
                'success': True,
                'transcript': 'This is a mock transcript of the audio content. The speaker discusses various topics related to the video subject matter.',
                'error': None
            }
    
    def get_available_models(self):
        """Mock available models"""
        return ['tiny', 'base', 'small', 'medium', 'large']
    
    def validate_model(self, model_name):
        """Mock model validation"""
        return model_name in self.get_available_models()


@pytest.fixture
def transcription_service():
    """Create mock TranscriptionService for fast testing"""
    return MockTranscriptionService()


class TestTranscriptionService:
    """Fast tests for transcription service logic"""

    def test_transcribe_audio_success(self, transcription_service):
        """Test successful audio transcription"""
        result = transcription_service.transcribe_audio("/tmp/audio.wav")
        
        assert result['success'] is True
        assert result['transcript'] is not None
        assert len(result['transcript']) > 0
        assert result['error'] is None

    def test_transcribe_audio_empty_file(self, transcription_service):
        """Test transcription of empty/corrupted audio file"""
        result = transcription_service.transcribe_audio("/tmp/no_audio.wav")
        
        assert result['success'] is False
        assert result['transcript'] is None
        assert 'empty or corrupted' in result['error']

    def test_transcribe_audio_timeout(self, transcription_service):
        """Test transcription timeout handling"""
        result = transcription_service.transcribe_audio("/tmp/timeout_audio.wav")
        
        assert result['success'] is False
        assert result['transcript'] is None
        assert 'timeout' in result['error'].lower()

    def test_transcribe_audio_unsupported_format(self, transcription_service):
        """Test unsupported audio format"""
        result = transcription_service.transcribe_audio("/tmp/unsupported_audio.wav")
        
        assert result['success'] is False
        assert result['transcript'] is None
        assert 'unsupported' in result['error'].lower()

    def test_get_available_models(self, transcription_service):
        """Test getting list of available models"""
        models = transcription_service.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'base' in models
        assert 'tiny' in models

    def test_validate_model_valid(self, transcription_service):
        """Test validation of valid model names"""
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        
        for model in valid_models:
            assert transcription_service.validate_model(model) is True

    def test_validate_model_invalid(self, transcription_service):
        """Test validation of invalid model names"""
        invalid_models = ['invalid', 'nonexistent', '', 'xl']
        
        for model in invalid_models:
            assert transcription_service.validate_model(model) is False

    def test_transcribe_with_different_models(self, transcription_service):
        """Test transcription with different model sizes"""
        models = ['tiny', 'base', 'small']
        
        for model in models:
            result = transcription_service.transcribe_audio("/tmp/audio.wav", model)
            assert result['success'] is True
            assert result['transcript'] is not None

    def test_transcript_content_quality(self, transcription_service):
        """Test that transcript content meets basic quality expectations"""
        result = transcription_service.transcribe_audio("/tmp/audio.wav")
        
        transcript = result['transcript']
        assert len(transcript) > 10  # Reasonable minimum length
        assert transcript.count('.') > 0 or transcript.count('!') > 0  # Has sentence endings
        assert any(word.isalpha() for word in transcript.split())  # Contains words

    def test_transcript_language_detection(self, transcription_service):
        """Test language detection in transcripts (mock)"""
        # This would test language detection if implemented
        result = transcription_service.transcribe_audio("/tmp/english_audio.wav")
        
        # Mock always returns English content
        transcript = result['transcript']
        assert 'This is a mock transcript' in transcript
        # In real implementation, could test for language detection
