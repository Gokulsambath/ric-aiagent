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

# Run migrations using the migration manager
echo "Running database migrations..."
./migration_manager.sh apply

# Show current migration status
echo "Current migration status:"
./migration_manager.sh status

# Prune unused
echo "Cleaning up..."
docker image prune -f
docker builder prune -f

echo "API Deployment Complete!"
