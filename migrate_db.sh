#!/bin/bash

echo "Running database migrations..."

# Check if container is running
if ! docker ps | grep -q ricagent-api; then
    echo "Error: ricagent-api container is not running"
    echo "Please start the container first with: docker-compose up -d ricagent-api"
    exit 1
fi

# Show current migration version
echo ""
echo "Current migration version:"
docker-compose exec -T ricagent-api alembic current

# Run migrations
echo ""
echo "Applying migrations..."
docker-compose exec -T ricagent-api alembic upgrade head

# Show new version
echo ""
echo "New migration version:"
docker-compose exec -T ricagent-api alembic current

# Verify monthly_updates table exists
echo ""
echo "Verifying monthly_updates table..."
docker-compose exec -T ricagent-api python -c "
from app.configs.database import get_db
from sqlalchemy import text

db = next(get_db())
result = db.execute(text(\"\"\"
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema='public' AND table_name='monthly_updates'
\"\"\"))
if result.fetchone():
    print('✅ monthly_updates table exists')
else:
    print('❌ monthly_updates table missing')
"

echo ""
echo "Migration complete!"
