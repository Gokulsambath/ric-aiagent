#!/bin/bash

echo "Starting API Deployment..."

# Pull latest changes
echo "Pulling latest changes from git..."
git pull

# Rebuild and restart container
echo "Rebuilding and restarting API container..."
docker-compose up -d --build ricagent-api

# Wait for container to be ready
echo "Waiting for container to be ready..."
sleep 5

# Run migrations explicitly
echo "Running database migrations..."
docker-compose exec -T ricagent-api alembic upgrade head

# Show current migration status
echo "Current migration status:"
docker-compose exec -T ricagent-api alembic current

# Prune unused
echo "Cleaning up..."
docker image prune -f
docker builder prune -f

echo "API Deployment Complete!"
