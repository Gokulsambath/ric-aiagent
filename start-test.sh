#!/bin/bash

# RicAgent Test Environment Startup Script
# This script starts all containers for the Test environment

set -e

echo "🧪 Starting RicAgent Test Environment..."

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

# Clean up any existing test data
echo "🧹 Cleaning up previous test data..."
docker-compose -f docker-compose-qa.yaml down -v 2>/dev/null || true

# Create network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create ricago-net 2>/dev/null || echo "Network ricago-net already exists"

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f docker-compose-qa.yaml pull

# Build custom images
echo "🔨 Building custom images for testing..."
docker-compose -f docker-compose-qa.yaml build --no-cache

# Start services
echo "🏗️  Starting services..."
docker-compose -f docker-compose-qa.yaml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check database initialization and seed data
echo "🌱 Checking database initialization..."
docker-compose -f docker-compose-qa.yaml exec -T ricagent-api python -c "from app.configs.database import get_db; next(get_db())" || {
    echo "⚠️  Database not ready yet, waiting longer..."
    sleep 30
}

echo "🌱 Seeding test database..."
docker-compose -f docker-compose-qa.yaml exec -T ricagent-api python -u -m app.utils.seed_widget_config || echo "⚠️  Seeding skipped or failed"

# Run additional test data seeding if available
echo "🧪 Setting up test data..."
docker-compose -f docker-compose-qa.yaml exec -T ricagent-api python -c "
try:
    from app.utils.test_data_seeder import seed_test_data
    seed_test_data()
    print('Test data seeded successfully')
except ImportError:
    print('No test data seeder found, skipping...')
except Exception as e:
    print(f'Test data seeding failed: {e}')
" || echo "⚠️  Test data seeding skipped"

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose-qa.yaml ps

# Run basic health checks
echo "🏥 Running health checks..."
sleep 10

# Test API endpoint
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5500/ | grep -q "200\|404"; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
fi

# Show useful URLs
echo ""
echo "🎉 RicAgent Test Environment is running!"
echo ""
echo "📍 Test Service URLs:"
echo "   🌐 API: http://localhost:5500"
echo "   🤖 Widget: http://localhost:3001" 
echo "   💬 Botpress: http://localhost:5600"
echo "   🗄️  PgAdmin: http://localhost:5055"
echo "   📊 Grafana: http://localhost:3005"
echo "   📈 Prometheus: http://localhost:9090"
echo "   🔍 Ollama: http://localhost:11343"
echo ""
echo "🧪 Test Environment Features:"
echo "   🧹 Clean database on startup"
echo "   🌱 Test data pre-seeded"
echo "   🏥 Automated health checks"
echo "   📊 Full monitoring enabled"
echo ""
echo "📝 To view logs: docker-compose -f docker-compose-qa.yaml logs -f [service_name]"
echo "🛑 To stop: docker-compose -f docker-compose-qa.yaml down"
echo "🗑️  To stop and remove volumes: docker-compose -f docker-compose-qa.yaml down -v"
echo ""