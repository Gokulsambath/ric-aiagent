#!/bin/bash
set -e

# Function to check if database is ready
check_db_ready() {
    python -c "from app.configs.database import get_db; next(get_db())" 2>/dev/null
}

echo "Waiting for database connection..."
while ! check_db_ready; do
    echo "Database not ready, waiting 2 seconds..."
    sleep 2
done
echo "Database connection established."

echo "Running database migration..."
# Using -u for unbuffered output to see logs in real-time
alembic upgrade head

echo "Seeding database..."
python -u -m app.utils.seed_widget_config

echo "Starting application with optimized settings..."
# Add performance optimizations for uvicorn
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --access-log \
    --log-level info \
    --loop uvloop \
    --http httptools
