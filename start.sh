#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Running Database Migrations ---"
# Run alembic migrations to ensure the database schema is up to date
alembic upgrade head

echo "--- Starting Gunicorn Server ---"
# Start Gunicorn with the optimized production configuration
# Binding to $PORT (provided by Cloud platforms like Railway) or default 8000
exec gunicorn -c gunicorn_conf.py app.main:app
