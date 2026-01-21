#!/bin/bash

# RicAgent Development Environment Startup Script
# This script starts all containers for the Development environment

set -e

echo "🚀 Starting RicAgent Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running again."
    exit 1
fi

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if the widget directory exists (for the frontend service)
if [ ! -d "../ric-aiagent-widget" ]; then
    echo "⚠️  Widget directory not found at ../ric-aiagent-widget"
    echo "   Please ensure ric-aiagent-widget is cloned in the same parent directory"
fi

# Create network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create ricago-net 2>/dev/null || echo "Network ricago-net already exists"

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f docker-compose.yml pull

# Build custom images with development optimizations
echo "🔨 Building custom images for development..."
docker-compose -f docker-compose.yml build --no-cache

# Start services
echo "🏗️  Starting services..."
docker-compose -f docker-compose.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check database initialization and seed data
echo "🌱 Checking database initialization..."
docker-compose -f docker-compose.yml exec -T ricagent-api python -c "from app.configs.database import get_db; next(get_db())" || {
    echo "⚠️  Database not ready yet, waiting longer..."
    sleep 30
}

echo "🌱 Seeding database if needed..."
docker-compose -f docker-compose.yml exec -T ricagent-api python -u -m app.utils.seed_widget_config || echo "⚠️  Seeding skipped or failed"

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.yml ps

# Show useful URLs
echo ""
echo "🎉 RicAgent Development Environment is running!"
echo ""
echo "📍 Development Service URLs:"
echo "   🌐 API: http://localhost:5500"
echo "   🤖 Widget: http://localhost:3001" 
echo "   💬 Botpress: http://localhost:5600"
echo "   🗄️  PgAdmin: http://localhost:5055"
echo "   📊 Grafana: http://localhost:3005"
echo "   📈 Prometheus: http://localhost:9090"
echo "   🔍 Ollama: http://localhost:11343"
echo ""
echo "🛠️  Development Features:"
echo "   📁 Hot reload enabled"
echo "   📝 Debug logs enabled"
echo "   🔧 Code volume mounts active"
echo ""
echo "📝 To view logs: docker-compose -f docker-compose.yml logs -f [service_name]"
echo "🛑 To stop: docker-compose -f docker-compose.yml down"
echo "🗑️  To stop and remove volumes: docker-compose -f docker-compose.yml down -v"
echo ""