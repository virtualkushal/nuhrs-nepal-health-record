FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# PyMySQL is a pure-Python MySQL driver, so no system MySQL client libs or
# compiler toolchain are needed here.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9002
CMD ["sh", "-c", "python manage.py makemigrations lab --noinput && python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-9002}"]
