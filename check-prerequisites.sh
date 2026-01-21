#!/bin/bash

# RicAgent QA Environment Prerequisites Checker
# This script checks if all prerequisites are met before running the containers

set -e

echo "🔍 Checking prerequisites for RicAgent QA Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "💡 Copying from .env.example"
    cp .env.example .env
    echo "✅ .env file created from example"
else
    echo "✅ .env file exists"
fi

# Check if docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
else
    echo "✅ Docker is running"
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
else
    echo "✅ Docker Compose is available"
fi

# Check if the widget directory exists
if [ ! -d "../ric-aiagent-widget" ]; then
    echo "⚠️  Widget directory not found at ../ric-aiagent-widget"
    echo "   The widget service will fail to build"
    echo "   Please ensure ric-aiagent-widget is in the same parent directory"
else
    echo "✅ Widget directory found"
fi

# Check required configuration files
required_files=(
    "nginx.conf"
    "init_db.sql"
    "requirements.txt"
    "Dockerfile"
    "monitoring/loki-config.yaml"
    "monitoring/prometheus.yaml"
    "monitoring/promtail-config.yaml"
    "monitoring/grafana-datasources.yaml"
    "monitoring/grafana-dashboards.yaml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
    fi
done

# Validate docker-compose configuration
if docker-compose -f docker-compose-qa.yaml config --quiet; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

# Check available disk space (need at least 5GB)
available_space=$(df . | awk 'NR==2{print $4}')
if [ "$available_space" -lt 5242880 ]; then  # 5GB in KB
    echo "⚠️  Low disk space. At least 5GB recommended for Docker images and volumes"
else
    echo "✅ Sufficient disk space available"
fi

# Check if ports are available
ports_to_check=(5500 3001 5600 5055 3005 9090 11343 6379 5435)
for port in "${ports_to_check[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
    else
        echo "✅ Port $port is available"
    fi
done

echo ""
echo "🎉 Prerequisites check completed!"
echo ""
echo "To start the QA environment, run:"
echo "   ./start-qa.sh"
echo ""