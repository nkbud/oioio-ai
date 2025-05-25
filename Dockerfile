FROM python:3.11-slim

# Install uv for Python package management
RUN pip install --upgrade pip && \
    pip install uv && \
    apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY pyproject.toml /app/
COPY oioio_mcp_agent/ /app/oioio_mcp_agent/

# Create directories
RUN mkdir -p /app/knowledge /app/.prefect

# Install dependencies with uv
RUN uv pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run as non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Default command
ENTRYPOINT ["python", "-m", "oioio_mcp_agent.cli"]
CMD ["--help"]