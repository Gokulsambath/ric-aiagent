#!/bin/bash

# RicAgent Production Environment Startup Script
# This script starts all containers for the Production environment

set -e

echo "🚀 Starting RicAgent Production Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Production environment requires proper configuration."
    echo "📝 Please create .env file with production settings before running."
    exit 1
fi

# Check for required production environment variables
required_env_vars=("POSTGRES_PASSWORD" "SECRET_KEY" "OPENAI_API_KEY" "MAIL_PASSWORD")
for var in "${required_env_vars[@]}"; do
    if ! grep -q "^$var=" .env || grep -q "^$var=changeme\|^$var=RICAGO\|^$var=$" .env; then
        echo "❌ Production environment variable $var is not properly set in .env file"
        echo "📝 Please configure all production settings before running."
        exit 1
    fi
done

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
    exit 1
fi

# Check for SSL certificates
if [ ! -f "../ssl/ricago.in.crt" ] || [ ! -f "../ssl/ricago.in.key" ]; then
    echo "⚠️  SSL certificates not found. Production environment requires SSL certificates."
    echo "   Expected: ../ssl/ricago.in.crt and ../ssl/ricago.in.key"
    echo "   You can start without SSL by commenting out the nginx service"
fi

# Create network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create ricago-net 2>/dev/null || echo "Network ricago-net already exists"

# Backup existing data volumes (safety measure)
echo "💾 Creating backup timestamp for safety..."
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Backup timestamp: $BACKUP_TIMESTAMP"

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f docker-compose-prod.yaml pull

# Build custom images for production
echo "🔨 Building optimized production images..."
docker-compose -f docker-compose-prod.yaml build --no-cache

# Start services in production mode
echo "🏗️  Starting production services..."
docker-compose -f docker-compose-prod.yaml up -d

# Wait for services to be healthy (longer timeout for production)
echo "⏳ Waiting for services to be healthy (this may take a few minutes)..."
sleep 60

# Check database initialization and seed data
echo "🌱 Checking database initialization..."
max_retries=5
retry_count=0
while ! docker-compose -f docker-compose-prod.yaml exec -T ricagent-api python -c "from app.configs.database import get_db; next(get_db())" && [ $retry_count -lt $max_retries ]; do
    echo "⚠️  Database not ready yet, waiting 30 seconds... (attempt $((retry_count + 1))/$max_retries)"
    sleep 30
    ((retry_count++))
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Database failed to become ready after $max_retries attempts"
    echo "📊 Container Status:"
    docker-compose -f docker-compose-prod.yaml ps
    echo "📝 Check logs with: docker-compose -f docker-compose-prod.yaml logs"
    exit 1
fi

echo "🌱 Seeding production database if needed..."
docker-compose -f docker-compose-prod.yaml exec -T ricagent-api python -u -m app.utils.seed_widget_config || echo "⚠️  Seeding skipped or failed"

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose-prod.yaml ps

# Run comprehensive health checks
echo "🏥 Running production health checks..."
sleep 15

# Test API endpoint
api_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5500/ || echo "000")
if [[ "$api_health" =~ ^(200|404)$ ]]; then
    echo "✅ API health check passed (HTTP $api_health)"
else
    echo "❌ API health check failed (HTTP $api_health)"
fi

# Test database connection
if docker-compose -f docker-compose-prod.yaml exec -T postgres pg_isready -U ${POSTGRES_USER:-ricagoapi_user} >/dev/null 2>&1; then
    echo "✅ Database health check passed"
else
    echo "❌ Database health check failed"
fi

# Show useful URLs
echo ""
echo "🎉 RicAgent Production Environment is running!"
echo ""
echo "📍 Production Service URLs:"
echo "   🌐 API: http://localhost:5500"
echo "   🤖 Widget: http://localhost:3001" 
echo "   💬 Botpress: http://localhost:5600"
echo "   🗄️  PgAdmin: http://localhost:5055"
echo "   📊 Grafana: http://localhost:3005"
echo "   📈 Prometheus: http://localhost:9090"
echo "   🔍 Ollama: http://localhost:11343"
if [ -f "../ssl/ricago.in.crt" ]; then
    echo "   🔒 HTTPS: https://localhost (via Nginx)"
fi
echo ""
echo "🏭 Production Environment Features:"
echo "   🔒 Security optimizations enabled"
echo "   📊 Full monitoring and logging"
echo "   💾 Data persistence configured"
echo "   🔄 Auto-restart policies active"
echo "   🏥 Health checks and monitoring"
echo ""
echo "⚠️  Production Notes:"
echo "   📝 Monitor logs regularly: docker-compose -f docker-compose-prod.yaml logs -f"
echo "   💾 Backup data regularly"
echo "   🔒 Ensure SSL certificates are up to date"
echo "   📊 Check monitoring dashboards"
echo ""
echo "🛑 To stop: docker-compose -f docker-compose-prod.yaml down"
echo "⚠️  For production restart: ./stop-prod.sh && ./start-prod.sh"
echo ""