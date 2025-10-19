"""
Audio Extraction Service

Extracts audio from video files using ffmpeg for transcription processing.
"""
import os
import re
import subprocess
import tempfile
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioExtractionService:
    """Service for extracting audio from video files using ffmpeg"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        
    def extract_audio(self, video_path: str, output_dir: str = None, timeout: int = 300) -> Dict[str, any]:
        """
        Extract audio from video file using ffmpeg
        
        Args:
            video_path: Path to the input video file
            output_dir: Directory to save extracted audio (default: temp dir)
            timeout: Maximum processing time in seconds
            
        Returns:
            Dict with success status, audio path, duration, and any errors
        """
        try:
            # Validate input file exists
            if not os.path.exists(video_path):
                return {
                    'success': False,
                    'audio_path': None,
                    'duration_seconds': None,
                    'error': f'Video file not found: {video_path}'
                }
            
            output_dir = output_dir or self.temp_dir
            
            # Generate safe output filename
            safe_filename = self._get_safe_filename(video_path)
            audio_path = os.path.join(output_dir, safe_filename)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # ffmpeg command to extract audio as WAV (good for Whisper)
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
                '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file if it exists
                audio_path
            ]
            
            logger.info(f"Extracting audio from {video_path} to {audio_path}")
            
            # Run ffmpeg with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = self._parse_ffmpeg_error(result.stderr)
                logger.error(f"FFmpeg failed: {error_msg}")
                return {
                    'success': False,
                    'audio_path': None,
                    'duration_seconds': None,
                    'error': error_msg
                }
            
            # Check if output file was created and has content
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                return {
                    'success': False,
                    'audio_path': None,
                    'duration_seconds': None,
                    'error': 'Audio extraction produced empty file - video may have no audio track'
                }
            
            # Parse duration from ffmpeg output
            duration = self._parse_duration(result.stderr)
            
            logger.info(f"Successfully extracted audio: {audio_path} ({duration}s)")
            
            return {
                'success': True,
                'audio_path': audio_path,
                'duration_seconds': duration,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Audio extraction timeout after {timeout}s")
            return {
                'success': False,
                'audio_path': None,
                'duration_seconds': None,
                'error': f'Audio extraction timeout after {timeout} seconds'
            }
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            return {
                'success': False,
                'audio_path': None,
                'duration_seconds': None,
                'error': f'Audio extraction failed: {str(e)}'
            }
    
    def _get_safe_filename(self, video_path: str) -> str:
        """Generate a safe filename for the extracted audio file"""
        base_name = os.path.basename(video_path)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # Replace unsafe characters with underscores
        safe_name = re.sub(r'[^\w\-_.]', '_', name_without_ext)
        
        return f"{safe_name}.wav"
    
    def _parse_duration(self, ffmpeg_output: str) -> Optional[float]:
        """Parse duration from ffmpeg stderr output"""
        try:
            # Look for duration in format: Duration: 00:02:30.45
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', ffmpeg_output)
            if duration_match:
                hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                return total_seconds
            return None
        except Exception as e:
            logger.warning(f"Could not parse duration: {e}")
            return None
    
    def _parse_ffmpeg_error(self, stderr: str) -> str:
        """Parse ffmpeg error messages to provide user-friendly feedback"""
        if not stderr:
            return "Unknown ffmpeg error"
        
        # Common error patterns
        if "No such file or directory" in stderr:
            return "Video file not found or cannot be accessed"
        elif "Stream map" in stderr and "matches no streams" in stderr:
            return "No audio track found in video file"
        elif "Invalid data found when processing input" in stderr:
            return "Video file appears to be corrupted or in unsupported format"
        elif "Permission denied" in stderr:
            return "Permission denied accessing video file"
        elif "Decoder" in stderr and "not found" in stderr:
            return "Video format not supported by ffmpeg"
        else:
            # Return the last line of stderr which usually contains the main error
            lines = stderr.strip().split('\n')
            return lines[-1] if lines else stderr[:200]
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up {file_path}: {e}")
    
    def get_video_info(self, video_path: str) -> Dict[str, any]:
        """Get basic information about a video file using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # Extract useful information
                format_info = info.get('format', {})
                streams = info.get('streams', [])
                
                audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
                video_streams = [s for s in streams if s.get('codec_type') == 'video']
                
                return {
                    'success': True,
                    'duration': float(format_info.get('duration', 0)),
                    'size_bytes': int(format_info.get('size', 0)),
                    'has_audio': len(audio_streams) > 0,
                    'has_video': len(video_streams) > 0,
                    'audio_codec': audio_streams[0].get('codec_name') if audio_streams else None,
                    'video_codec': video_streams[0].get('codec_name') if video_streams else None,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': f'ffprobe failed: {result.stderr}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Video info extraction failed: {str(e)}'
            }
