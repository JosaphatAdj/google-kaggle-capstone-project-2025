# ============================================================
# ROBONEST EMBEDDED ROBOT - DOCKERFILE
# Robot Agent with A2A Client
# ============================================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY embedded_robot/ ./embedded_robot/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/status || exit 1

# Run robot
CMD ["python", "-u", "embedded_robot/main_a2a.py"]
