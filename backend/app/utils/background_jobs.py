"""
Background Job Queue for Long-Running Operations

Provides a simple async job queue for processing long-running tasks
without blocking API responses.

Implements Requirement 17.4: Background job queue for long operations
"""
import asyncio
import logging
from typing import Callable, Any, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Represents a background job"""
    
    def __init__(
        self,
        job_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        description: str = ""
    ):
        """
        Initialize a job
        
        Args:
            job_id: Unique job identifier
            func: Async function to execute
            args: Positional arguments for function
            kwargs: Keyword arguments for function
            description: Human-readable job description
        """
        self.job_id = job_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.description = description
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[str] = None
        self.progress: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary representation"""
        return {
            "job_id": self.job_id,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "error": self.error
        }


class BackgroundJobQueue:
    """
    Async job queue for background processing
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1 - Background job queue
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize job queue
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, Job] = {}
        self.workers: list = []
        self.running = False
    
    async def start(self):
        """Start the job queue workers"""
        if self.running:
            logger.warning("Job queue already running")
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
        
        logger.info(f"Started job queue with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the job queue workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for all workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Stopped job queue")
    
    async def _worker(self, worker_id: int):
        """
        Worker coroutine that processes jobs from the queue
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get job from queue with timeout
                try:
                    job = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process job
                await self._process_job(job, worker_id)
                
                # Mark task as done
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _process_job(self, job: Job, worker_id: int):
        """
        Process a single job
        
        Args:
            job: Job to process
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} processing job {job.job_id}: {job.description}")
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        try:
            # Execute job function
            result = await job.func(*job.args, **job.kwargs)
            
            # Mark as completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.progress = 1.0
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            # Mark as failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            
            logger.error(f"Job {job.job_id} failed: {e}")
    
    async def submit(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        description: str = "",
        job_id: Optional[str] = None
    ) -> str:
        """
        Submit a job to the queue
        
        Args:
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            description: Job description
            job_id: Optional job ID (generated if not provided)
            
        Returns:
            Job ID
        """
        if not self.running:
            raise RuntimeError("Job queue is not running")
        
        # Generate job ID if not provided
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        # Create job
        job = Job(
            job_id=job_id,
            func=func,
            args=args,
            kwargs=kwargs,
            description=description
        )
        
        # Store job
        self.jobs[job_id] = job
        
        # Add to queue
        await self.queue.put(job)
        
        logger.info(f"Submitted job {job_id}: {description}")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None if not found
        """
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary or None if not found
        """
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        return None
    
    def get_all_jobs(self) -> list:
        """
        Get all jobs
        
        Returns:
            List of job dictionaries
        """
        return [job.to_dict() for job in self.jobs.values()]
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Remove completed jobs older than max_age_hours
        
        Args:
            max_age_hours: Maximum age in hours for completed jobs
        """
        now = datetime.utcnow()
        to_remove = []
        
        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at:
                    age_hours = (now - job.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")


# Global job queue instance
job_queue = BackgroundJobQueue(max_workers=5)


async def start_job_queue():
    """Start the global job queue"""
    await job_queue.start()


async def stop_job_queue():
    """Stop the global job queue"""
    await job_queue.stop()


async def submit_job(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    description: str = ""
) -> str:
    """
    Submit a job to the global job queue
    
    Args:
        func: Async function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        description: Job description
        
    Returns:
        Job ID
    """
    return await job_queue.submit(func, args, kwargs, description)


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a job
    
    Args:
        job_id: Job ID
        
    Returns:
        Job status dictionary or None
    """
    return job_queue.get_job_status(job_id)
