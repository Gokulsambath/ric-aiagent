#!/bin/bash

echo "Starting Infrastructure variables (Postgres, Botpress)..."
docker compose up -d

echo "Infrastructure started."
docker compose ps
