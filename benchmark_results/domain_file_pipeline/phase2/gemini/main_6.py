from pydantic import BaseModel
from typing import Optional, Dict, Any

class JobResponse(BaseModel):
    """Response model for the /upload endpoint."""
    job_id: str
    status: str

class StatusResponse(BaseModel):
    """Response model for the /status/{job_id} endpoint."""
    job_id: str
    status: str
    details: Optional[Dict[str, Any]] = None