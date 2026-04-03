from fastapi import FastAPI, UploadFile, File, HTTPException, status
from . import schemas, tasks

app = FastAPI(
    title="File Pipeline API",
    version="1.0.0",
    description="An API to upload files and track their processing status asynchronously."
)

@app.post("/upload", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload(file: UploadFile = File(...)):
    """
    Accepts a file for asynchronous processing.
    
    The file is sent to a background worker, and a job ID is returned immediately.
    """
    # Note: For a real application, you would save the file to a temporary location
    # or a cloud storage like S3 before passing the reference to the task.
    # Reading the whole file into memory is not scalable for large files.
    file_contents = await file.read() # Read file content for processing
    
    task = tasks.process_file.delay(
        filename=file.filename,
        content_type=file.content_type,
        size=len(file_contents)
    )
    
    return {"job_id": task.id, "status": "accepted"}


@app.get("/status/{job_id}", response_model=schemas.StatusResponse)
async def get_status(job_id: str):
    """
    Retrieves the status of a processing job.
    
    Use the job_id returned by the /upload endpoint.
    """
    status_info = tasks.get_task_status(job_id)
    
    # Celery's state for a non-existent task is PENDING.
    # We check if result is None to be more explicit.
    if status_info["status"] == "PENDING" and status_info["details"] is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return status_info