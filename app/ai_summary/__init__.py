"""
AI Summary Services Package

This package provides services for generating AI summaries of video content:
- Audio extraction from video files (ffmpeg)
- Speech transcription (Whisper)  
- Text summarization (Ollama)
- Background task management
"""

# Lazy imports to avoid NumPy compatibility issues on startup
def get_audio_service():
    """Lazy import of AudioExtractionService"""
    from .audio_extraction import AudioExtractionService
    return AudioExtractionService

def get_transcription_service():
    """Lazy import of TranscriptionService"""
    from .transcription import TranscriptionService
    return TranscriptionService

def get_summarization_service():
    """Lazy import of SummarizationService"""
    from .summarization import SummarizationService
    return SummarizationService

def get_task_queue():
    """Lazy import of TaskQueue"""
    from .task_queue import TaskQueue, get_task_queue
    return get_task_queue()

__all__ = [
    'get_audio_service',
    'get_transcription_service', 
    'get_summarization_service',
    'get_task_queue'
]
