from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    filename: Optional[str] = None
    file_size: Optional[int] = None
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    filename: str
    file_size: int
    file_path: str
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None