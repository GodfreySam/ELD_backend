FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev only needed for Postgres; removed for SQLite-only setup
# RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=api.settings

# Render sets $PORT dynamically; run migrations then start Gunicorn
CMD ["bash", "-lc", "python manage.py migrate --noinput && (python manage.py seed_sample || true) && gunicorn api.wsgi:application --bind 0.0.0.0:$PORT --workers 3"]
