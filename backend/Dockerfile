# ── Backend Dockerfile ──────────────────────────────────────────────
FROM python:3.11-slim AS backend

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint system dependencies + PostgreSQL client (for pg_isready healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        libcairo2 \
        libglib2.0-0 \
        shared-mime-info \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files (silently)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Entrypoint: run migrations then start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn auditoria.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
