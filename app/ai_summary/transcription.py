"""
Transcription Service

Converts audio files to text using OpenAI Whisper.
"""
import os
import logging
import tempfile
from typing import Dict, Optional, List
import whisper
from pathlib import Path

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using Whisper"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize transcription service
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Whisper model (lazy loading)"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Successfully loaded Whisper model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model {self.model_name}: {e}")
            self.model = None
    
    def transcribe_audio(self, audio_path: str, language: str = None) -> Dict[str, any]:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es') or None for auto-detection
            
        Returns:
            Dict with success status, transcript text, and any errors
        """
        try:
            # Validate input file
            if not os.path.exists(audio_path):
                return {
                    'success': False,
                    'transcript': None,
                    'language': None,
                    'error': f'Audio file not found: {audio_path}'
                }
            
            # Check file size (Whisper has practical limits)
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size_mb > 200:  # 200MB limit
                return {
                    'success': False,
                    'transcript': None,
                    'language': None,
                    'error': f'Audio file too large: {file_size_mb:.1f}MB (max 200MB)'
                }
            
            # Check if file has content
            if os.path.getsize(audio_path) == 0:
                return {
                    'success': False,
                    'transcript': None,
                    'language': None,
                    'error': 'Audio file is empty'
                }
            
            # Ensure model is loaded
            if self.model is None:
                self._load_model()
                if self.model is None:
                    return {
                        'success': False,
                        'transcript': None,
                        'language': None,
                        'error': f'Could not load Whisper model: {self.model_name}'
                    }
            
            logger.info(f"Transcribing audio file: {audio_path}")
            
            # Transcribe the audio
            result = self.model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                verbose=False
            )
            
            transcript_text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            if not transcript_text:
                return {
                    'success': False,
                    'transcript': None,
                    'language': detected_language,
                    'error': 'No speech detected in audio file'
                }
            
            logger.info(f"Successfully transcribed audio ({detected_language}): {len(transcript_text)} characters")
            
            return {
                'success': True,
                'transcript': transcript_text,
                'language': detected_language,
                'confidence': self._estimate_confidence(result),
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                'success': False,
                'transcript': None,
                'language': None,
                'error': f'Transcription failed: {str(e)}'
            }
    
    def _estimate_confidence(self, whisper_result: dict) -> Optional[float]:
        """Estimate transcription confidence from Whisper result"""
        try:
            # Whisper doesn't provide direct confidence scores,
            # but we can estimate based on segment data
            segments = whisper_result.get('segments', [])
            if not segments:
                return None
            
            # Average the no_speech_prob (lower is better)
            no_speech_probs = [seg.get('no_speech_prob', 0.5) for seg in segments]
            avg_no_speech_prob = sum(no_speech_probs) / len(no_speech_probs)
            
            # Convert to confidence (higher is better)
            confidence = 1.0 - avg_no_speech_prob
            return round(confidence, 3)
            
        except Exception as e:
            logger.warning(f"Could not estimate confidence: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large"]
    
    def validate_model(self, model_name: str) -> bool:
        """Validate if model name is supported"""
        return model_name in self.get_available_models()
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """Get information about a Whisper model"""
        model_info = {
            "tiny": {
                "parameters": "39 M",
                "vram_required": "~1 GB",
                "relative_speed": "~32x",
                "description": "Fastest, least accurate"
            },
            "base": {
                "parameters": "74 M", 
                "vram_required": "~1 GB",
                "relative_speed": "~16x",
                "description": "Good balance of speed and accuracy"
            },
            "small": {
                "parameters": "244 M",
                "vram_required": "~2 GB", 
                "relative_speed": "~6x",
                "description": "Better accuracy, moderate speed"
            },
            "medium": {
                "parameters": "769 M",
                "vram_required": "~5 GB",
                "relative_speed": "~2x", 
                "description": "High accuracy, slower"
            },
            "large": {
                "parameters": "1550 M",
                "vram_required": "~10 GB",
                "relative_speed": "1x",
                "description": "Highest accuracy, slowest"
            }
        }
        
        return model_info.get(model_name)
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different Whisper model"""
        if not self.validate_model(model_name):
            logger.error(f"Invalid model name: {model_name}")
            return False
        
        if model_name == self.model_name:
            logger.info(f"Already using model: {model_name}")
            return True
        
        try:
            logger.info(f"Switching from {self.model_name} to {model_name}")
            self.model_name = model_name
            self._load_model()
            return self.model is not None
        except Exception as e:
            logger.error(f"Failed to switch to model {model_name}: {e}")
            return False
    
    def transcribe_with_timestamps(self, audio_path: str, language: str = None) -> Dict[str, any]:
        """
        Transcribe audio with word-level timestamps
        
        Args:
            audio_path: Path to the audio file
            language: Language code or None for auto-detection
            
        Returns:
            Dict with transcript and detailed timing information
        """
        try:
            if self.model is None:
                self._load_model()
                if self.model is None:
                    return {
                        'success': False,
                        'error': f'Could not load Whisper model: {self.model_name}'
                    }
            
            logger.info(f"Transcribing with timestamps: {audio_path}")
            
            result = self.model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                verbose=False,
                word_timestamps=True
            )
            
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', '').strip(),
                    'words': segment.get('words', [])
                })
            
            return {
                'success': True,
                'transcript': result.get('text', '').strip(),
                'language': result.get('language', 'unknown'),
                'segments': segments,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Timestamped transcription failed: {str(e)}")
            return {
                'success': False,
                'error': f'Timestamped transcription failed: {str(e)}'
            }
