import json
import redis
from datetime import datetime
from typing import Optional
from src.config import settings
from src.models import JobInfo, JobStatus

class JobService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    def create_job(self, job_id: str, filename: str, file_size: int, file_path: str) -> JobInfo:
        """Create a new job entry"""
        job_info = JobInfo(
            job_id=job_id,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            filename=filename,
            file_size=file_size,
            file_path=file_path
        )
        
        # Store job info in Redis
        self.redis_client.hset(
            f"job:{job_id}",
            mapping={
                "data": job_info.model_dump_json(),
                "status": job_info.status.value,
                "created_at": job_info.created_at.isoformat(),
                "updated_at": job_info.updated_at.isoformat()
            }
        )
        
        # Set expiration for job data (24 hours)
        self.redis_client.expire(f"job:{job_id}", 86400)
        
        return job_info
    
    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information by ID"""
        job_data = self.redis_client.hget(f"job:{job_id}", "data")
        if not job_data:
            return None
        
        return JobInfo.model_validate_json(job_data)
    
    def update_job_status(self, job_id: str, status: JobStatus, progress: int = 0, 
                         result: Optional[dict] = None, error_message: Optional[str] = None):
        """Update job status and progress"""
        job_info = self.get_job(job_id)
        if not job_info:
            return False
        
        job_info.status = status
        job_info.updated_at = datetime.utcnow()
        job_info.progress = progress
        
        if result:
            job_info.result = result
        if error_message:
            job_info.error_message = error_message
        
        # Update Redis
        self.redis_client.hset(
            f"job:{job_id}",
            mapping={
                "data": job_info.model_dump_json(),
                "status": status.value,
                "updated_at": job_info.updated_at.isoformat()
            }
        )
        
        return True

job_service = JobService()