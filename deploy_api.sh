#!/bin/bash

echo "Starting API Deployment..."

# Pull latest changes
echo "Pulling latest changes from git..."
git pull

# Rebuild and restart container
echo "Rebuilding and restarting API container..."
docker-compose up -d --build ricagent-api

# Prune unused
echo "Cleaning up..."
docker image prune -f
docker builder prune -f

echo "API Deployment Complete!"
