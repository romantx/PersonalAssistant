# File Pipeline API

This project is an implementation of a simple file processing pipeline API based on the provided OpenAPI specification. It uses FastAPI for the web server and Celery with Redis for asynchronous background processing.

## Architecture

- **`api`**: A FastAPI web server that exposes two endpoints:
  - `POST /upload`: Accepts a file and queues it for processing. Returns a `202 Accepted` status with a `job_id`.
  - `GET /status/{job_id}`: Returns the current status of a processing job.
- **`worker`**: A Celery worker that listens for tasks on the Redis queue and executes the file processing logic.
- **`redis`**: A Redis instance that acts as both the message broker for Celery (to queue tasks) and the result backend (to store task status and results).

## Prerequisites

- Docker
- Docker Compose

## How to Run the Service

1.  **Clone the repository.**

2.  **Build and start the services using Docker Compose:**

    ```bash
    docker-compose up --build
    ```

    This will:
    - Build the Python application Docker image.
    - Start the `redis` container.
    - Start the `api` container, accessible on `http://localhost:8000`.
    - Start the `worker` container, which will connect to Redis and wait for tasks.

## How to Use the API

You can interact with the API using tools like `curl` or by visiting the auto-generated documentation.

### Interactive Docs (Swagger UI)

Once the service is running, open your browser and navigate to:
[http://localhost:8000/docs](http://localhost:8000/docs)

You can try out the API directly from this interface.

### Using `curl`

1.  **Upload a file:**
    Create a sample file named `my-file.txt`.

    ```bash
    echo "This is the content of my test file." > my-file.txt
    ```

    Now, upload it to the API:

    ```bash
    curl -X POST -F "file=@my-file.txt" http://localhost:8000/upload
    ```

    You will receive a JSON response similar to this:
    ```json
    {
      "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
      "status": "accepted"
    }
    ```

2.  **Check the status:**
    Copy the `job_id` from the previous step and use it to query the status endpoint. The processing task is simulated to take 10 seconds.

    ```bash
    # Replace a1b2c3d4-... with your actual job_id
    curl http://localhost:8000/status/a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890
    ```

    - **Immediately after upload (or if the job is in progress):**
      ```json
      {
        "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
        "status": "PROCESSING",
        "details": {
          "details": "Step 3 of 10 completed.",
          "current": 3,
          "total": 10
        }
      }
      ```

    - **After the job is complete (after ~10 seconds):**
      ```json
      {
        "job_id": "a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890",
        "status": "SUCCESS",
        "details": {
          "details": "Successfully processed my-file.txt",
          "filename": "my-file.txt",
          "content_type": "text/plain",
          "size": 39
        }
      }
      ```

## How to Run Tests

The tests are designed to be run inside the container to ensure the environment is consistent.

1.  Make sure the services are running (`docker-compose up`).

2.  In a separate terminal, execute `pytest` inside the `api` service container:

    ```bash
    docker-compose exec api pytest
    ```

    You should see the test results indicating that all tests have passed.