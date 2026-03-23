FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY nixclaw/ ./nixclaw/
COPY TASK.md ./

# Create working directories
RUN mkdir -p /tmp/agent_workdir /var/log/autogen-agent /tmp/autogen-agent

# Default environment variables
ENV LOG_LEVEL=info
ENV DEBUG_MODE=false
ENV COMMAND_EXECUTOR_WORKING_DIR=/tmp/agent_workdir
ENV STORAGE_LOGS_DIR=/var/log/autogen-agent
ENV STORAGE_TEMP_DIR=/tmp/autogen-agent

ENTRYPOINT ["python", "-m", "nixclaw"]
