#!/bin/bash
set -e

echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Database is ready. Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 shortener.wsgi:application
