import time
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.celery_worker import celery_app

# Configure Celery for testing: run tasks synchronously
celery_app.conf.update(task_always_eager=True)

client = TestClient(app)

def test_upload_and_status_pipeline():
    """
    Tests the full upload -> status check pipeline.
    """
    # 1. Upload a file
    file_content = b"This is a test file."
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response_upload = client.post("/upload", files=files)
    
    assert response_upload.status_code == 202
    data = response_upload.json()
    assert "job_id" in data
    assert data["status"] == "accepted"
    job_id = data["job_id"]
    
    # 2. Check status immediately (it should be completed due to task_always_eager=True)
    response_status = client.get(f"/status/{job_id}")
    
    assert response_status.status_code == 200
    status_data = response_status.json()
    
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "SUCCESS"
    assert "details" in status_data
    assert status_data["details"]["filename"] == "test.txt"
    assert status_data["details"]["size"] == len(file_content)

def test_get_status_for_nonexistent_job():
    """
    Tests that a 404 is returned for a job_id that does not exist.
    """
    non_existent_job_id = "this-id-does-not-exist"
    response = client.get(f"/status/{non_existent_job_id}")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}

@patch('app.tasks.process_file.delay')
def test_upload_endpoint_calls_celery_task(mock_delay):
    """
    Unit test to ensure the /upload endpoint correctly calls the Celery task.
    """
    # Set up the mock to behave like a real Celery AsyncResult
    mock_delay.return_value.id = "mock-job-id-123"
    
    file_content = b"mock file"
    files = {"file": ("mock.txt", file_content, "text/plain")}
    
    response_upload = client.post("/upload", files=files)
    
    # Assert the endpoint returned the correct response
    assert response_upload.status_code == 202
    assert response_upload.json()["job_id"] == "mock-job-id-123"
    
    # Assert that our Celery task's delay method was called once with the correct arguments
    mock_delay.assert_called_once_with(
        filename="mock.txt",
        content_type="text/plain",
        size=len(file_content)
    )
