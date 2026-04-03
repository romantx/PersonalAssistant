import time
from celery.result import AsyncResult
from .celery_worker import celery_app

@celery_app.task(bind=True)
def process_file(self, filename: str, content_type: str, size: int):
    """
    A mock task that simulates processing a file.
    It updates its state to 'PROCESSING' and then 'SUCCESS'.
    """
    total_steps = 10
    self.update_state(
        state='PROCESSING',
        meta={'details': f"Starting processing for {filename} ({size} bytes).", 'current': 0, 'total': total_steps}
    )
    
    for i in range(total_steps):
        time.sleep(1) # Simulate one second of work
        self.update_state(
            state='PROCESSING',
            meta={'details': f"Step {i+1} of {total_steps} completed.", 'current': i + 1, 'total': total_steps}
        )
    
    # Final result
    return {
        'details': f"Successfully processed {filename}",
        'filename': filename,
        'content_type': content_type,
        'size': size
    }

def get_task_status(task_id: str):
    """Helper function to get the status and result of a Celery task."""
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "job_id": task_id,
        "status": task_result.state,
        "details": task_result.info if task_result.info else None
    }
    return response