FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8090
# Migrate, seed demo data + index it nationally, then serve. Seeding/pushing are
# idempotent enough for the demo and no-op quietly if already done.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_demo && python manage.py nuhrs_push && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8090}"]
