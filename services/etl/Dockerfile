# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for layer caching)
COPY pyproject.toml setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY app ./app

# Copy start script
COPY start.sh ./
RUN chmod +x start.sh

# Set Python path to include app directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Start command - use uvicorn directly (Railway sets PORT automatically)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
