FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
# Install sentry-sdk and alembic explicitly if not in requirements
RUN pip install --no-cache-dir -r requirements.txt sentry-sdk alembic psycopg2-binary gunicorn

# Copy application code
COPY . .
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Start command
ENTRYPOINT ["./entrypoint.sh"]
