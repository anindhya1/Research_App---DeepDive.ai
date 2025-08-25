FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p static/exports templates

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "gunicorn --worker-class gevent --workers 1 --timeout 300 --bind 0.0.0.0:${PORT:-8000} wsgi:app"]