"""
AI Summary Coordinator

Orchestrates the complete video summarization workflow:
1. Extract audio from video
2. Transcribe audio to text  
3. Generate summary from text
4. Store results in database
"""
import os
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from sqlalchemy import or_

# Lazy imports to avoid NumPy issues on startup
# Services will be imported only when get_coordinator() is called

logger = logging.getLogger(__name__)


class VideoSummaryCoordinator:
    """Coordinates the complete video summarization workflow"""
    
    def __init__(self):
        # Lazy initialization - services created on first access
        self._audio_service = None
        self._transcription_service = None
        self._summarization_service = None
        self._task_queue = None
        
        # Configuration
        self.temp_audio_cleanup = True
        
        logger.info("VideoSummaryCoordinator initialized with lazy loading.")
        
    @property
    def audio_service(self):
        """Lazy load AudioExtractionService"""
        if self._audio_service is None:
            from .audio_extraction import AudioExtractionService
            self._audio_service = AudioExtractionService()
        return self._audio_service
    
    @property
    def transcription_service(self):
        """Lazy load TranscriptionService"""
        if self._transcription_service is None:
            from .transcription import TranscriptionService
            self._transcription_service = TranscriptionService(model_name="base")
        return self._transcription_service
    
    @property
    def summarization_service(self):
        """Lazy load SummarizationService"""
        if self._summarization_service is None:
            from .summarization import SummarizationService
            self._summarization_service = SummarizationService()
        return self._summarization_service
    
    @property
    def task_queue(self):
        """Lazy load TaskQueue"""
        if self._task_queue is None:
            from .task_queue import get_task_queue
            self._task_queue = get_task_queue()
            # Register the video summary handler
            self._task_queue.register_handler('video_summary', self._process_video_summary_task)
        return self._task_queue
    
    def start_video_summary(self, video_path: str, user_id: str = None, force: bool = False, model_name: str = None) -> Dict[str, Any]:
        """
        Start video summarization process (async)
        
        Args:
            video_path: Path to the video file
            user_id: Optional user ID for tracking
            force: If True, regenerate even if a completed summary exists
            
        Returns:
            Dict with task information
        """
        try:
            # Validate video file exists
            if not os.path.exists(video_path):
                def _short_model(name: str) -> str:
                    try:
                        if not name:
                            return ''
                        short = name.split('+')[-1]
                        return short.replace('-instruct', '')
                    except Exception:
                        return name or ''

                def _format_date(dt) -> str:
                    try:
                        d = dt.strftime('%m/%d/%y')
                        return d
                    except Exception:
                        return ''

                # Helper fallbacks
                def _fallback_model(v_row):
                    try:
                        return v_row.model_used or video_summary.model_used
                    except Exception:
                        return video_summary.model_used

                return {
                    'success': False,
                    'error': f'Video file not found: {video_path}'
                }
            
            # Check if summary already exists or create new one (atomic operation)
            from ..database import SessionLocal, VideoSummary
            db = SessionLocal()
            try:
                existing = db.query(VideoSummary).filter(
                    VideoSummary.video_path == video_path
                ).first()
                
                if existing:
                    if existing.status == 'completed' and not force:
                        return {
                            'success': False,
                            'error': 'Summary already exists for this video',
                            'existing_summary': {
                                'status': existing.status,
                                'summary': existing.summary,
                                'generated_at': existing.generated_at.isoformat()
                            }
                        }
                    elif existing.status in ['pending', 'processing'] and not force:
                        return {
                            'success': False,
                            'error': 'Summary generation already in progress for this video',
                            'existing_task': {
                                'status': existing.status,
                                'generated_at': existing.generated_at.isoformat()
                            }
                        }
                    # For force or failed/no_audio we reset to pending
                    existing.status = 'pending'
                    existing.error_message = None
                    existing.generated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(existing)
                    summary_id = existing.id
                    logger.info(f"(Re)starting summary for {video_path} (ID: {summary_id}) force={force}")
                else:
                    # No existing record, create new one
                    video_summary = VideoSummary(
                        video_path=video_path,
                        status='pending'
                    )
                    db.add(video_summary)
                    db.commit()
                    db.refresh(video_summary)
                    summary_id = video_summary.id
                    logger.info(f"Created new summary record for {video_path} (ID: {summary_id})")
            except Exception as e:
                db.rollback()
                logger.error(f"Database error in start_video_summary: {e}")
                return {
                    'success': False,
                    'error': f'Database error: {str(e)}'
                }
            finally:
                db.close()
            
            # Add task to queue
            task_data = {
                'video_path': video_path,
                'summary_id': summary_id,
                'user_id': user_id,
                'model_name': model_name
            }
            task_id = self.task_queue.add_task('video_summary', task_data)
            
            logger.info(f"Started video summary task {task_id} for {video_path}")
            
            return {
                'success': True,
                'task_id': task_id,
                'status': 'processing',
                'message': 'Video summary generation started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start video summary: {e}")
            return {
                'success': False,
                'error': f'Failed to start video summary: {str(e)}'
            }
    
    def _process_video_summary_task(self, task) -> Dict[str, Any]:
        """
        Process video summary task (called by task queue)
        
        Args:
            task: Task object from the task queue
            
        Returns:
            Dict with processing results
        """
        video_path = task.data['video_path']
        summary_id = task.data['summary_id']
        user_id = task.data.get('user_id')
        model_name = task.data.get('model_name')
        
        # Create progress callback that updates the task
        def progress_callback(message: str, percent: int = None):
            task.progress = message
            if percent is not None:
                task.progress_percent = percent
        
        return self._process_video_summary(video_path, summary_id, user_id, progress_callback, model_name=model_name)
    
    def _process_video_summary(self, video_path: str, summary_id: int, user_id: str = None, progress_callback=None, model_name: str = None) -> Dict[str, Any]:
        """
        Process video summary task (called by task queue)
        
        Args:
            video_path: Path to the video file
            summary_id: Database ID of the VideoSummary record
            user_id: Optional user ID for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with processing results
        """
        
        logger.info(f"Processing video summary for {video_path}")
        start_time = datetime.utcnow()
        temp_files = []
        
        try:
            # Update database status
            self._update_summary_status(summary_id, 'processing', 'Starting video analysis...')
            if progress_callback:
                progress_callback('Starting video analysis...', 0)
            
            # Step 1: Extract audio
            if progress_callback:
                progress_callback('🎵 Extracting audio from video file...', 5)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                if progress_callback:
                    progress_callback('🔧 Setting up audio extraction with FFmpeg...', 8)
                
                audio_result = self.audio_service.extract_audio(video_path, temp_dir)
                
                if progress_callback:
                    progress_callback('✅ Audio extraction completed', 15)
                
                if not audio_result['success']:
                    # Handle no audio case specifically
                    if 'no audio' in audio_result['error'].lower():
                        self._update_summary_status(
                            summary_id, 'no_audio', 
                            error_message='Video file has no audio track'
                        )
                        return {
                            'success': False,
                            'error': 'Video has no audio track',
                            'status': 'no_audio'
                        }
                    else:
                        raise Exception(f"Audio extraction failed: {audio_result['error']}")
                
                audio_path = audio_result['audio_path']
                audio_duration = audio_result['duration_seconds']
                temp_files.append(audio_path)
                
                logger.info(f"Extracted audio: {audio_duration}s")
                
                # Step 2: Transcribe audio
                if progress_callback:
                    progress_callback(f'🎤 Loading Whisper AI model ({self.transcription_service.model_name})...', 20)
                
                if progress_callback:
                    progress_callback(f'🗣️ Transcribing {audio_duration:.1f}s of audio to text...', 25)
                
                transcription_result = self.transcription_service.transcribe_with_timestamps(audio_path)
                
                if progress_callback:
                    progress_callback('✅ Audio transcription completed', 50)
                
                if not transcription_result['success']:
                    raise Exception(f"Transcription failed: {transcription_result['error']}")
                
                transcript = transcription_result['transcript']
                detected_language = transcription_result.get('language', 'unknown')
                segments = transcription_result.get('segments', [])
                
                logger.info(f"Transcribed audio ({detected_language}): {len(transcript)} characters")
                
                # Step 3: Generate summary
                if progress_callback:
                    progress_callback(f'📝 Preparing transcript ({len(transcript)} characters)...', 55)
                
                if progress_callback:
                    progress_callback('🤖 Loading Ollama language model...', 60)
                
                if progress_callback:
                    progress_callback('🧠 Generating comprehensive AI summary...', 65)
                
                summary_result = self.summarization_service.summarize_transcript(transcript, model_name=model_name)
                
                if progress_callback:
                    progress_callback('✅ AI summary generation completed', 85)
                
                if not summary_result['success']:
                    raise Exception(f"Summarization failed: {summary_result['error']}")
                
                summary_text = summary_result['summary']
                model_used = f"whisper-{self.transcription_service.model_name}+{summary_result.get('model_used', 'llama3.2:7b')}"
                
                logger.info(f"Generated summary: {len(summary_text)} characters")
                
                # Step 4: Store results
                if progress_callback:
                    progress_callback('💾 Saving summary to database...', 90)
                
                if progress_callback:
                    progress_callback('🔄 Finalizing and cleaning up...', 95)
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update database with results
                from ..database import SessionLocal, VideoSummary, VideoSummaryVersion
                db = SessionLocal()
                try:
                    video_summary = db.query(VideoSummary).filter(
                        VideoSummary.id == summary_id
                    ).first()
                    
                    if video_summary:
                        video_summary.summary = summary_text
                        # Build curated jump points using the LLM with heuristic fallback
                        from json import dumps as _dumps
                        ai_jump_points = []
                        try:
                            ai_jump_points = self.summarization_service.generate_jump_points(
                                segments=segments,
                                transcript=transcript,
                                model_name=model_name,
                                max_points=10
                            ) or []
                        except Exception:
                            ai_jump_points = []

                        # Heuristic fallback: pick up to 8 spaced, keyword-biased moments
                        if not ai_jump_points:
                            import re
                            kw = re.compile(r"intro|introduction|overview|setup|install|configure|demo|example|concept|definition|recap|summary|conclusion|best practice|tip|troubleshoot|issue", re.I)
                            candidates = []
                            for seg in segments or []:
                                try:
                                    s = float(seg.get('start', 0))
                                    text = (seg.get('text') or '').strip()
                                except Exception:
                                    continue
                                if not text:
                                    continue
                                score = 0
                                if kw.search(text):
                                    score += 2
                                score += min(1.0, len(text) / 200.0)
                                candidates.append((score, int(max(0, round(s))), text))
                            # Sort by score desc, then spread across time
                            candidates.sort(key=lambda x: -x[0])
                            top = candidates[:20]
                            top.sort(key=lambda x: x[1])
                            # Downsample evenly to at most 8
                            if len(top) > 8:
                                step = max(1, len(top) // 8)
                                top = top[::step][:8]
                            ai_jump_points = [{
                                'seconds': t,
                                'title': (txt.split('. ')[0] if txt else '').strip()[:100] or 'Jump'
                            } for _, t, txt in top]

                        video_summary.transcript = transcript
                        if ai_jump_points:
                            video_summary.transcript += f"\n\n[JUMP_POINTS]{_dumps(ai_jump_points)}"
                        video_summary.status = 'completed'
                        video_summary.model_used = model_used
                        video_summary.processing_time_seconds = processing_time
                        video_summary.audio_duration_seconds = audio_duration
                        video_summary.error_message = None
                        # Create a new version row
                        # Next version = (current max version for this path) + 1
                        current_max = db.query(VideoSummaryVersion).filter(
                            VideoSummaryVersion.video_path == video_summary.video_path
                        ).order_by(VideoSummaryVersion.version.desc()).first()
                        next_ver = (current_max.version + 1) if current_max else 1
                        db.add(VideoSummaryVersion(
                            video_path=video_summary.video_path,
                            version=next_ver,
                            summary=summary_text,
                            # Persist transcript including embedded curated jump points for this version
                            transcript=video_summary.transcript,
                            model_used=model_used,
                            processing_time_seconds=processing_time
                        ))
                        
                        db.commit()
                        logger.info(f"Saved summary to database (ID: {summary_id})")
                finally:
                    db.close()
                
                # Cleanup temp files
                if self.temp_audio_cleanup:
                    self.audio_service.cleanup_temp_files(temp_files)
                
                if progress_callback:
                    progress_callback('Completed successfully', 100)
                
                return {
                    'success': True,
                    'summary_id': summary_id,
                    'summary': summary_text,
                    'transcript_length': len(transcript),
                    'processing_time': processing_time,
                    'audio_duration': audio_duration,
                    'language': detected_language,
                    'model_used': model_used
                }
        
        except Exception as e:
            logger.error(f"Video summary processing failed: {e}")
            
            # Update database with error
            self._update_summary_status(
                summary_id, 'failed', 
                error_message=str(e)
            )
            
            # Cleanup temp files
            if self.temp_audio_cleanup:
                self.audio_service.cleanup_temp_files(temp_files)
            
            return {
                'success': False,
                'error': str(e),
                'summary_id': summary_id
            }
    
    def _update_summary_status(self, summary_id: int, status: str, progress: str = None, error_message: str = None):
        """Update database summary status"""
        try:
            from ..database import SessionLocal, VideoSummary
            db = SessionLocal()
            try:
                video_summary = db.query(VideoSummary).filter(
                    VideoSummary.id == summary_id
                ).first()
                
                if video_summary:
                    video_summary.status = status
                    if error_message:
                        video_summary.error_message = error_message
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to update summary status: {e}")
    
    def get_summary_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a summary generation task"""
        return self.task_queue.get_task_status(task_id)

    def find_active_task_for_video(self, video_path: str) -> Optional[str]:
        """Find an active (pending/processing) task id for a given video path"""
        try:
            # Lazy import to avoid circulars
            from .task_queue import TaskStatus
            tq = self.task_queue
            for tid, task in list(tq.tasks.items()):
                if task.task_type != 'video_summary':
                    continue
                if task.data.get('video_path') != video_path:
                    continue
                if task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
                    return tid
            return None
        except Exception:
            return None
    
    def get_video_summary(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get completed summary for a video"""
        try:
            from ..database import SessionLocal, VideoSummary, VideoSummaryVersion
            db = SessionLocal()
            try:
                # Try exact path first, then fallback to suffix match to handle base-dir changes
                rel = video_path.split('/')[-1] if '/' in video_path else video_path
                video_summary = db.query(VideoSummary).filter(
                    or_(
                        VideoSummary.video_path == video_path,
                        VideoSummary.video_path.like(f"%/{rel}"),
                        VideoSummary.video_path.like(f"%\\{rel}")
                    )
                ).order_by(VideoSummary.generated_at.desc()).first()
                
                if not video_summary:
                    return None
                # Ensure at least v1 exists if we have a completed summary but no versions yet
                versions_q = db.query(VideoSummaryVersion).filter(
                    VideoSummaryVersion.video_path == video_path
                ).order_by(VideoSummaryVersion.version.desc())
                versions_list = versions_q.all()
                if (video_summary.summary and video_summary.status == 'completed' and not versions_list):
                    db.add(VideoSummaryVersion(
                        video_path=video_summary.video_path,
                        version=1,
                        summary=video_summary.summary,
                        transcript=video_summary.transcript,
                        model_used=video_summary.model_used
                    ))
                    db.commit()
                    versions_list = versions_q.all()

                # Build versions list and attach processing time for the latest version if available
                latest_version = None
                versions_list = versions_q.all()
                if versions_list:
                    latest_version = versions_list[0].version

                return {
                    'video_path': video_summary.video_path,
                    'summary': video_summary.summary,
                    'transcript': video_summary.transcript,
                    'status': video_summary.status,
                    'error_message': video_summary.error_message,
                    'model_used': video_summary.model_used,
                    'generated_at': video_summary.generated_at.isoformat(),
                    'processing_time_seconds': video_summary.processing_time_seconds,
                    'audio_duration_seconds': video_summary.audio_duration_seconds,
                    'versions': [
                        {
                            'version': v.version,
                            'generated_at': v.generated_at.isoformat(),
                            'model_used': (v.model_used or video_summary.model_used),
                            'display_model': (v.model_used or video_summary.model_used),
                            'processing_time_seconds': (v.processing_time_seconds if v.processing_time_seconds is not None else (video_summary.processing_time_seconds if latest_version and v.version == latest_version else None)),
                            'display_label': (
                                f"v{v.version} • "
                                f"{(v.generated_at.strftime('%m/%d/%y') if hasattr(v.generated_at, 'strftime') else str(v.generated_at))}"
                                + (
                                    f" • {round(((v.processing_time_seconds if v.processing_time_seconds is not None else (video_summary.processing_time_seconds or 0)))/60, 1)}m"
                                    if ((v.processing_time_seconds is not None) or (latest_version and v.version == latest_version and video_summary.processing_time_seconds))
                                    else ''
                                )
                            )
                        }
                        for v in versions_list
                    ]
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to get video summary: {e}")
            return None

    def list_versions_for_video(self, video_path: str) -> List[Dict[str, Any]]:
        """Return version metadata for a video, tolerant to base path changes."""
        try:
            from ..database import SessionLocal, VideoSummaryVersion, VideoSummary
            db = SessionLocal()
            try:
                rel = video_path.split('/')[-1] if '/' in video_path else video_path
                versions = db.query(VideoSummaryVersion).filter(
                    or_(
                        VideoSummaryVersion.video_path == video_path,
                        VideoSummaryVersion.video_path.like(f"%/{rel}"),
                        VideoSummaryVersion.video_path.like(f"%\\{rel}")
                    )
                ).order_by(VideoSummaryVersion.version.desc()).all()
                # Also try to fetch latest processing time from VideoSummary if available
                latest = db.query(VideoSummary).filter(
                    or_(
                        VideoSummary.video_path == video_path,
                        VideoSummary.video_path.like(f"%/{rel}"),
                        VideoSummary.video_path.like(f"%\\{rel}")
                    )
                ).order_by(VideoSummary.generated_at.desc()).first()
                latest_ver = None
                if versions:
                    latest_ver = versions[0].version
                result = []
                for v in versions:
                    # Fallback model name if version row missing it
                    model_name = v.model_used or (latest.model_used if latest else None)
                    # Prefer per-version processing time if present; otherwise fallback to latest if matching version
                    proc_time = v.processing_time_seconds if v.processing_time_seconds is not None else (
                        latest.processing_time_seconds if (latest and latest_ver == v.version) else None
                    )
                    result.append({
                        'version': v.version,
                        'generated_at': v.generated_at.isoformat(),
                        'model_used': model_name,
                        'display_model': model_name,
                        'processing_time_seconds': proc_time
                    })
                return result
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to list versions for video: {e}")
            return []

    def get_video_summary_version(self, video_path: str, version: int) -> Optional[Dict[str, Any]]:
        """Get a specific version of the summary for a video"""
        try:
            from ..database import SessionLocal, VideoSummaryVersion
            from sqlalchemy import or_
            db = SessionLocal()
            try:
                # Tolerant match: exact path or suffix match to handle base-dir changes
                rel = video_path.split('/')[-1] if '/' in video_path else video_path
                v = db.query(VideoSummaryVersion).filter(
                    VideoSummaryVersion.version == version,
                    or_(
                        VideoSummaryVersion.video_path == video_path,
                        VideoSummaryVersion.video_path.like(f"%/{rel}"),
                        VideoSummaryVersion.video_path.like(f"%\\{rel}")
                    )
                ).first()
                if not v:
                    return None
                return {
                    'video_path': v.video_path,
                    'summary': v.summary,
                    'transcript': v.transcript,
                    'model_used': v.model_used,
                    'generated_at': v.generated_at.isoformat(),
                    'version': v.version
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to get summary version: {e}")
            return None
    
    def delete_video_summary(self, video_path: str) -> Dict[str, Any]:
        """Delete a video summary"""
        try:
            from ..database import SessionLocal, VideoSummary
            db = SessionLocal()
            try:
                video_summary = db.query(VideoSummary).filter(
                    VideoSummary.video_path == video_path
                ).first()
                
                if not video_summary:
                    return {
                        'success': False,
                        'error': 'Summary not found'
                    }
                
                db.delete(video_summary)
                db.commit()
                
                return {
                    'success': True,
                    'message': 'Summary deleted successfully'
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to delete video summary: {e}")
            return {
                'success': False,
                'error': f'Failed to delete summary: {str(e)}'
            }
    
    def list_video_summaries(self, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List video summaries with optional filtering"""
        try:
            from ..database import SessionLocal, VideoSummary
            db = SessionLocal()
            try:
                query = db.query(VideoSummary).order_by(VideoSummary.generated_at.desc())
                
                if status:
                    query = query.filter(VideoSummary.status == status)
                
                summaries = query.limit(limit).all()
                
                return [
                    {
                        'video_path': s.video_path,
                        'status': s.status,
                        'generated_at': s.generated_at.isoformat(),
                        'processing_time_seconds': s.processing_time_seconds,
                        'has_summary': bool(s.summary),
                        'error_message': s.error_message
                    }
                    for s in summaries
                ]
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to list video summaries: {e}")
            return []
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary generation statistics"""
        try:
            from ..database import SessionLocal, VideoSummary
            from sqlalchemy import func
            
            db = SessionLocal()
            try:
                # Count by status
                status_counts = db.query(
                    VideoSummary.status,
                    func.count(VideoSummary.id).label('count')
                ).group_by(VideoSummary.status).all()
                
                status_dict = {status: count for status, count in status_counts}
                
                # Processing time statistics
                avg_processing_time = db.query(
                    func.avg(VideoSummary.processing_time_seconds)
                ).filter(VideoSummary.status == 'completed').scalar() or 0
                
                total_processing_time = db.query(
                    func.sum(VideoSummary.processing_time_seconds)
                ).filter(VideoSummary.status == 'completed').scalar() or 0
                
                # Count videos with audio
                videos_with_audio = db.query(VideoSummary).filter(
                    VideoSummary.status != 'no_audio'
                ).count()
                
                return {
                    'total_summaries': sum(status_dict.values()),
                    'completed': status_dict.get('completed', 0),
                    'failed': status_dict.get('failed', 0),
                    'processing': status_dict.get('processing', 0),
                    'no_audio': status_dict.get('no_audio', 0),
                    'average_processing_time': round(avg_processing_time, 1),
                    'total_processing_time': round(total_processing_time, 1),
                    'videos_with_audio': videos_with_audio,
                    'status_breakdown': status_dict
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to get summary statistics: {e}")
            return {
                'total_summaries': 0,
                'error': str(e)
            }


# Global coordinator instance
_coordinator = None


def get_coordinator() -> VideoSummaryCoordinator | None:
    """Get the global coordinator instance; under pytest return None by default.
    Tests patch this function when they need a fake coordinator.
    """
    try:
        import sys as _sys
        if 'pytest' in _sys.modules:
            return None
    except Exception:
        pass
    global _coordinator
    if _coordinator is None:
        _coordinator = VideoSummaryCoordinator()
    return _coordinator
