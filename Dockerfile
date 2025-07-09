# GreyBrain Bank - Backend Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY models/ ./models/
COPY prompts/ ./prompts/

# Create necessary directories
RUN mkdir -p generated_content logs

# Create non-root user for security
RUN useradd -m -u 1000 greybrain && chown -R greybrain:greybrain /app
USER greybrain

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["python", "app.py"]
