# Multi-stage Dockerfile for GPU-enabled repomap-tool (DEFAULT)
# Stage 1: Base image with Python (works on both x86_64 and arm64)
ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE} AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package configuration first for better caching
COPY pyproject.toml ./

# Install pip-tools and generate requirements.txt
RUN pip install pip-tools toml && pip-compile pyproject.toml --output-file requirements.txt

# Create a hash of the requirements for the image tag
RUN echo "deps-$(sha256sum requirements.txt | cut -d' ' -f1 | head -c 12)" > .deps-hash

# Install PyTorch with platform-specific support
# This will automatically detect and use CUDA on x86_64 or MPS on arm64
RUN pip install torch torchvision torchaudio

# Install other production dependencies
RUN pip install -r requirements.txt

# Install additional dependencies for CodeRankEmbed
RUN pip install einops

# Download and cache CodeRankEmbed model (happens at build time)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/CodeRankEmbed', trust_remote_code=True)"

# Set environment variable for embedding model
ENV REPOMAP_EMBEDDING_MODEL=nomic-ai/CodeRankEmbed

# Stage 2: Final image with package
FROM base AS final

# Copy source code (this layer will be cached unless source changes)
COPY src/ ./src/

# Install the package in editable mode (without reinstalling dependencies)
RUN pip install -e . --no-deps

# Set environment variables
ENV PYTHONPATH=/app
#ENV REPOMAP_WORKSPACE_DIR=/workspace
ENV CACHE_DIR=/workspace/.repomap/cache
ENV REPOMAP_SESSION_DIR=/workspace/.repomap/sessions

# Copy and set up the entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set entrypoint to the shell wrapper
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]

WORKDIR /workspace
