# Dockerfile
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

# App dir
WORKDIR /app

# Install Python deps early for cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Ensure necessary directories exist
RUN mkdir -p static/exports templates

# Ensure Flask binds externally and respects $PORT on platforms like Cloud Run/Spaces
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose container port
EXPOSE 8000

# Use gunicorn with gevent but fix the timeout and worker config
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--worker-connections", "1000", "--timeout", "300", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "wsgi:app"]