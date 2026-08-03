FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Migrations are committed to the repo (core/migrations), so we only APPLY them
# here. We intentionally do NOT run makemigrations at runtime: generating
# migrations against an existing database can silently skip schema changes
# (Django sees 0001_initial as already applied and never adds new columns).
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py bootstrap && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]


