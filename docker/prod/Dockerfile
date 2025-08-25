# Dockerfile
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

# Install Python dependencies
RUN pip install -e .

# Install aider-chat from PyPI (no need to copy parent directory)
RUN pip install aider-chat

# Copy the repomap script and matchers
COPY src/external_repomap.py .
COPY src/matchers/fuzzy_matcher.py .
COPY src/matchers/adaptive_semantic_matcher.py .
COPY src/matchers/hybrid_matcher.py .
COPY src/matchers/semantic_matcher.py .
COPY docker/scripts/entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create a volume for persistent cache
VOLUME ["/app/cache"]

# Set environment variables
ENV PYTHONPATH=/app
ENV CACHE_DIR=/app/cache

# Default command
ENTRYPOINT ["./entrypoint.sh"]
