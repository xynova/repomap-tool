# Dockerfile for Docker RepoMap Tool
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package configuration first for better caching
COPY pyproject.toml ./

# Install pip-tools and generate requirements.txt
RUN pip install pip-tools && pip-compile pyproject.toml --output-file requirements.txt

# Install production dependencies only (without the package itself)
RUN pip install -r requirements.txt

# Copy source code (this layer will be cached unless source changes)
COPY src/ ./src/

# Install the package in editable mode (without reinstalling dependencies)
RUN pip install -e . --no-deps

# Create a volume for persistent cache
VOLUME ["/app/cache"]

# Set environment variables
ENV PYTHONPATH=/app
ENV CACHE_DIR=/app/cache

# Set entrypoint to the Python module
ENTRYPOINT ["python", "-m", "repomap_tool.cli"]
