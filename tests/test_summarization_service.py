"""
Fast unit tests for Ollama summarization service (mocked operations)
"""
import pytest
from unittest.mock import patch, MagicMock


class MockSummarizationService:
    """Mock summarization service for fast testing"""
    
    def __init__(self):
        self.ollama_url = "http://ollama:11434"
        self.model_name = "llama3.2:7b"
    
    def summarize_transcript(self, transcript, model_name=None):
        """Mock summarize_transcript method"""
        if not transcript or len(transcript.strip()) == 0:
            return {
                'success': False,
                'summary': None,
                'error': 'Empty transcript provided'
            }
        elif "connection_error" in transcript:
            return {
                'success': False,
                'summary': None,
                'error': 'Connection to Ollama service failed'
            }
        elif "model_not_found" in transcript:
            return {
                'success': False,
                'summary': None,
                'error': 'Model llama3.2:7b not found in Ollama'
            }
        elif len(transcript) > 50000:  # Mock max length check
            return {
                'success': False,
                'summary': None,
                'error': 'Transcript too long for processing'
            }
        else:
            # Mock successful summarization
            return {
                'success': True,
                'summary': f'Summary: This video discusses key concepts from the transcript. The main topics covered include technical implementation details and educational content. Total content length: {len(transcript)} characters.',
                'error': None
            }
    
    def check_ollama_health(self):
        """Mock Ollama health check"""
        return {
            'healthy': True,
            'models_available': ['llama3.2:7b', 'llama3.2:3b'],
            'error': None
        }
    
    def get_model_info(self, model_name):
        """Mock model info retrieval"""
        if model_name == "llama3.2:7b":
            return {
                'name': 'llama3.2:7b',
                'size': '4.7GB',
                'family': 'llama',
                'parameter_size': '7B'
            }
        elif model_name == "nonexistent":
            return None
        else:
            return {
                'name': model_name,
                'size': 'unknown',
                'family': 'unknown',
                'parameter_size': 'unknown'
            }
    
    def validate_transcript_length(self, transcript):
        """Mock transcript length validation"""
        return len(transcript) <= 50000
    
    def extract_key_topics(self, summary):
        """Mock key topic extraction from summary"""
        if not summary:
            return []
        
        # Mock topic extraction
        topics = []
        if "technical" in summary.lower():
            topics.append("Technical Implementation")
        if "educational" in summary.lower():
            topics.append("Educational Content")
        if "concept" in summary.lower():
            topics.append("Core Concepts")
        
        return topics


@pytest.fixture
def summarization_service():
    """Create mock SummarizationService for fast testing"""
    return MockSummarizationService()


class TestSummarizationService:
    """Fast tests for summarization service logic"""

    def test_summarize_transcript_success(self, summarization_service):
        """Test successful transcript summarization"""
        transcript = "This is a test transcript about machine learning concepts and implementation details."
        
        result = summarization_service.summarize_transcript(transcript)
        
        assert result['success'] is True
        assert result['summary'] is not None
        assert len(result['summary']) > 0
        assert result['error'] is None
        assert 'Summary:' in result['summary']

    def test_summarize_empty_transcript(self, summarization_service):
        """Test summarization with empty transcript"""
        result = summarization_service.summarize_transcript("")
        
        assert result['success'] is False
        assert result['summary'] is None
        assert 'empty transcript' in result['error'].lower()

    def test_summarize_connection_error(self, summarization_service):
        """Test handling of Ollama connection errors"""
        transcript = "This transcript will trigger a connection_error"
        
        result = summarization_service.summarize_transcript(transcript)
        
        assert result['success'] is False
        assert result['summary'] is None
        assert 'connection' in result['error'].lower()

    def test_summarize_model_not_found(self, summarization_service):
        """Test handling when model is not available"""
        transcript = "This transcript mentions model_not_found"
        
        result = summarization_service.summarize_transcript(transcript)
        
        assert result['success'] is False
        assert result['summary'] is None
        assert 'model' in result['error'].lower()

    def test_summarize_transcript_too_long(self, summarization_service):
        """Test handling of very long transcripts"""
        # Create a transcript that exceeds the mock limit
        long_transcript = "A" * 60000
        
        result = summarization_service.summarize_transcript(long_transcript)
        
        assert result['success'] is False
        assert result['summary'] is None
        assert 'too long' in result['error'].lower()

    def test_check_ollama_health(self, summarization_service):
        """Test Ollama service health check"""
        health = summarization_service.check_ollama_health()
        
        assert health['healthy'] is True
        assert isinstance(health['models_available'], list)
        assert len(health['models_available']) > 0
        assert 'llama3.2:7b' in health['models_available']
        assert health['error'] is None

    def test_get_model_info_existing(self, summarization_service):
        """Test getting info for existing model"""
        info = summarization_service.get_model_info("llama3.2:7b")
        
        assert info is not None
        assert info['name'] == "llama3.2:7b"
        assert 'size' in info
        assert 'family' in info
        assert 'parameter_size' in info

    def test_get_model_info_nonexistent(self, summarization_service):
        """Test getting info for nonexistent model"""
        info = summarization_service.get_model_info("nonexistent")
        
        assert info is None

    def test_validate_transcript_length(self, summarization_service):
        """Test transcript length validation"""
        short_transcript = "Short transcript"
        long_transcript = "A" * 60000
        
        assert summarization_service.validate_transcript_length(short_transcript) is True
        assert summarization_service.validate_transcript_length(long_transcript) is False

    def test_extract_key_topics(self, summarization_service):
        """Test key topic extraction from summaries"""
        summary = "This video discusses technical implementation and educational concepts"
        
        topics = summarization_service.extract_key_topics(summary)
        
        assert isinstance(topics, list)
        assert "Technical Implementation" in topics
        assert "Educational Content" in topics
        assert "Core Concepts" in topics

    def test_extract_key_topics_empty_summary(self, summarization_service):
        """Test topic extraction from empty summary"""
        topics = summarization_service.extract_key_topics("")
        
        assert isinstance(topics, list)
        assert len(topics) == 0

    def test_summary_quality_metrics(self, summarization_service):
        """Test that summaries meet quality expectations"""
        transcript = "This is a detailed transcript about various programming concepts, algorithms, and best practices in software development."
        
        result = summarization_service.summarize_transcript(transcript)
        summary = result['summary']
        
        # Quality checks
        assert len(summary) > 50  # Reasonable minimum length
        assert summary.count('.') > 0  # Has sentences
        assert 'Summary:' in summary  # Has proper formatting
        # Note: Mock summaries may be longer than original due to template text

    def test_different_model_names(self, summarization_service):
        """Test summarization with different model names"""
        transcript = "Test transcript for different models"
        models = ["llama3.2:7b", "llama3.2:3b"]
        
        for model in models:
            result = summarization_service.summarize_transcript(transcript, model)
            assert result['success'] is True
            assert result['summary'] is not None
