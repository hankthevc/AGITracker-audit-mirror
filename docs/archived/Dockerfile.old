# Dockerfile for AGI Tracker ETL Service
# Designed to be run from repository root with services/etl as build context
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including supervisor for process management
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for layer caching)
COPY services/etl/pyproject.toml services/etl/setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy shared packages directory (needed for scoring logic)
COPY packages /app/packages

# Copy application code from services/etl
COPY services/etl/app ./app

# Copy migrations and alembic config
COPY infra/migrations ./migrations
COPY infra/migrations/alembic.ini ./alembic.ini

# Copy supervisor configuration
COPY services/etl/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set Python path to include app directory and packages
ENV PYTHONPATH=/app:/app/packages/scoring/python:$PYTHONPATH

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Start command - use supervisor to manage all processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
