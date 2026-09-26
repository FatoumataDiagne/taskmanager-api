#!/bin/sh
set -e

echo "Applying database migrations..."
flask db upgrade

echo "Starting Gunicorn..."
exec gunicorn run:app --bind 0.0.0.0:5000 --workers 2