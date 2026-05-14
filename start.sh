#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Crucial: Ensure the 'app' directory is in the python path
export PYTHONPATH=$PYTHONPATH:.

echo "--- Running Database Migrations ---"
# Run alembic migrations using python -m to ensure the current path is included
python -m alembic upgrade head

echo "--- Starting Gunicorn Server ---"
# Start Gunicorn with the optimized production configuration
# Binding to $PORT (provided by Cloud platforms like Railway) or default 8000
exec gunicorn -c gunicorn_conf.py app.main:app
