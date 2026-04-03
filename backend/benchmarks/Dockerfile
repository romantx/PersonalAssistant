# Pinned base image for strict reproducibility
FROM python:3.12-slim@sha256:dlt-update-me-to-latest-sha-later

# Create non-root user for executing untrusted model code
RUN useradd --create-home --shell /bin/bash sandbox

# Set working directory
WORKDIR /app

# Install benchmarking tools globally
COPY requirements-bench.txt .
RUN pip install --no-cache-dir -r requirements-bench.txt

# The model's generated code will be mounted into /app/generated_code
# and the Phase 2 test suite will be mounted into /app/tests
# The entrypoint can be overridden by the runner script to execute specific tools

# Ensure sandbox user owns the working directory
RUN chown -R sandbox:sandbox /app

# Drop to sandbox user
USER sandbox

# Default command placeholder; runner script will override
CMD ["echo", "Container ready for evaluation"]
