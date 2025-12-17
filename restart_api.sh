#!/bin/bash

# Define service name
SERVICE_NAME="ricagent-api"

echo "Stopping and rebuilding $SERVICE_NAME..."

# Build and recreate ONLY the api service
# --no-deps: Don't start linked services (postgres, botpress)
# --build: Build images before starting containers
docker compose up -d --no-deps --build $SERVICE_NAME

echo "$SERVICE_NAME has been rebuilt and restarted."
docker compose ps | grep $SERVICE_NAME
