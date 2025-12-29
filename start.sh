#!/bin/bash
set -e

echo "Running database migration (bot_id)..."
# Using -u for unbuffered output to see logs in real-time
python -u -m app.db.migrate_bot_id

echo "Seeding database..."
python -u -m app.db.seed_widget_config

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
