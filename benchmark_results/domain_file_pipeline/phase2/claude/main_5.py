import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from celery import Celery
from src.config import settings
from src.models import JobStatus
from src.services.job_service import job_service

# Initialize Celery
celery_app = Celery(
    "file_pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.services.file_service"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "src.services.file_service.process_file_task": "file_processing"
    }
)

class FileService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file"""
        # Check file extension
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in settings.allowed_extensions:
            return False, f"File extension {file_ext} not allowed. Allowed extensions: {settings.allowed_extensions}"
        
        # Check file size (this is a basic check, actual size will be verified during upload)
        if hasattr(file, 'size') and file.size and file.size > settings.max_file_size:
            return False, f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        
        return True, None
    
    async def save_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """Save uploaded file and return job_id, file_path, and file_size"""
        # Generate unique job ID and filename
        job_id = str(uuid.uuid4())
        file_ext = Path(file.filename or "").suffix.lower()
        safe_filename = f"{job_id}{file_ext}"
        file_path = self.upload_dir / safe_filename
        
        # Save file
        content = await file.read()
        file_size = len(content)
        
        # Check file size after reading
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size {file_size} exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        return job_id, str(file_path), file_size
    
    def submit_processing_job(self, job_id: str, filename: str, file_size: int, file_path: str) -> str:
        """Submit file processing job to Celery"""
        # Create job record
        job_service.create_job(job_id, filename, file_size, file_path)
        
        # Submit to Celery
        process_file_task.delay(job_id, file_path)
        
        return job_id

@celery_app.task(name="src.services.file_service.process_file_task")
def process_file_task(job_id: str, file_path: str):
    """Background task to process uploaded file"""
    try:
        # Update status to processing
        job_service.update_job_status(job_id, JobStatus.PROCESSING, progress=10)
        
        # Simulate file processing steps
        import time
        
        # Step 1: File analysis
        time.sleep(2)
        job_service.update_job_status(job_id, JobStatus.PROCESSING, progress=30)
        
        # Step 2: Content extraction
        time.sleep(3)
        job_service.update_job_status(job_id, JobStatus.PROCESSING, progress=60)
        
        # Step 3: Processing
        time.sleep(2)
        job_service.update_job_status(job_id, JobStatus.PROCESSING, progress=80)
        
        # Step 4: Generate results
        file_stats = os.stat(file_path)
        file_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        
        result = {
            "processed_at": datetime.utcnow().isoformat(),
            "file_size": file_stats.st_size,
            "file_hash": file_hash.hexdigest(),
            "processing_duration": "7 seconds",
            "status": "Successfully processed"
        }
        
        time.sleep(1)
        job_service.update_job_status(job_id, JobStatus.COMPLETED, progress=100, result=result)
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        error_message = f"Processing failed: {str(e)}"
        job_service.update_job_status(job_id, JobStatus.FAILED, error_message=error_message)
        raise

file_service = FileService()