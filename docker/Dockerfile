# Dockerfile for Docker RepoMap Tool
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package configuration
COPY pyproject.toml setup.py ./

# Copy the entire source code
COPY src/ ./src/

# Install Python dependencies and the package
RUN pip install --upgrade pip setuptools wheel
RUN pip install -e .

# No entrypoint script needed - use direct CLI commands

# Create a volume for persistent cache
VOLUME ["/app/cache"]

# Set environment variables
ENV PYTHONPATH=/app
ENV CACHE_DIR=/app/cache

# Default command - show help
CMD ["repomap-tool", "--help"]
