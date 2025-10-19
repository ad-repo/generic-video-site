"""
Task Queue System

Simple in-memory task queue for background AI summary processing.
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Represents a background task"""
    
    def __init__(self, task_id: str, task_type: str, data: Dict[str, Any], callback: Callable = None):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.callback = callback
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.progress = ""
        self.progress_percent = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'progress_percent': self.progress_percent,
            'result': self.result,
            'error': self.error,
            'data': self.data
        }


class TaskQueue:
    """Simple in-memory task queue with background worker"""
    
    def __init__(self, max_workers: int = 2):
        self.tasks: Dict[str, Task] = {}
        self.pending_tasks: List[str] = []
        self.max_workers = max_workers
        self.active_workers = 0
        self.lock = threading.Lock()
        self.running = False
        self.worker_thread = None
        
        # Task handlers
        self.handlers: Dict[str, Callable] = {}
    
    def start(self):
        """Start the background worker"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Task queue worker started")
    
    def stop(self):
        """Stop the background worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Task queue worker stopped")
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler function for a task type"""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def add_task(self, task_type: str, data: Dict[str, Any], callback: Callable = None) -> str:
        """
        Add a new task to the queue
        
        Args:
            task_type: Type of task (e.g., 'video_summary')
            data: Task data/parameters
            callback: Optional callback function when task completes
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        with self.lock:
            task = Task(task_id, task_type, data, callback)
            self.tasks[task_id] = task
            self.pending_tasks.append(task_id)
        
        logger.info(f"Added task {task_id} of type {task_type}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status information"""
        task = self.get_task(task_id)
        return task.to_dict() if task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                if task_id in self.pending_tasks:
                    self.pending_tasks.remove(task_id)
                return True
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        with self.lock:
            status_counts = {}
            for task in self.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_tasks': len(self.tasks),
            'pending_tasks': len(self.pending_tasks),
            'active_workers': self.active_workers,
            'max_workers': self.max_workers,
            'running': self.running,
            'status_counts': status_counts
        }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.completed_at and task.completed_at.timestamp() < cutoff_time:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]
                
            logger.info(f"Cleaned up {len(to_remove)} old tasks")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                # Check if we can start a new task
                if self.active_workers >= self.max_workers:
                    time.sleep(1)
                    continue
                
                # Get next pending task
                task_id = None
                with self.lock:
                    if self.pending_tasks:
                        task_id = self.pending_tasks.pop(0)
                
                if task_id:
                    # Process the task in a separate thread
                    worker_thread = threading.Thread(
                        target=self._process_task,
                        args=(task_id,),
                        daemon=True
                    )
                    worker_thread.start()
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
    
    def _process_task(self, task_id: str):
        """Process a single task"""
        task = self.get_task(task_id)
        if not task:
            return
        
        with self.lock:
            self.active_workers += 1
        
        try:
            # Mark task as processing
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            
            logger.info(f"Processing task {task_id} of type {task.task_type}")
            
            # Get handler for this task type
            handler = self.handlers.get(task.task_type)
            if not handler:
                raise Exception(f"No handler registered for task type: {task.task_type}")
            
            # Execute the handler
            result = handler(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.progress = "Completed"
            task.progress_percent = 100
            
            # Call callback if provided
            if task.callback:
                try:
                    task.callback(task)
                except Exception as e:
                    logger.error(f"Task callback error: {e}")
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            # Mark as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            task.progress = f"Failed: {str(e)}"
            
            logger.error(f"Task {task_id} failed: {e}")
            
        finally:
            with self.lock:
                self.active_workers -= 1
    
    def update_task_progress(self, task_id: str, progress: str, percent: int = None):
        """Update task progress"""
        task = self.get_task(task_id)
        if task:
            task.progress = progress
            if percent is not None:
                task.progress_percent = max(0, min(100, percent))


# Global task queue instance
_task_queue = None


def get_task_queue() -> TaskQueue:
    """Get the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=2)
        _task_queue.start()
    return _task_queue


def shutdown_task_queue():
    """Shutdown the global task queue"""
    global _task_queue
    if _task_queue:
        _task_queue.stop()
        _task_queue = None
