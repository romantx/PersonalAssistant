import os
from celery import Celery

# Get Redis URLs from environment variables with defaults
broker_url = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
result_backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")

# Create a Celery instance
celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=result_backend_url,
    include=['app.tasks'] # Tell celery where to find tasks
)

celery_app.conf.update(
    task_track_started=True,
)