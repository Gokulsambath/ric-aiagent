#!/bin/bash
# Migration management script for RIC AI Agent
# This script helps manage database migrations in the Docker environment

set -e

CONTAINER_NAME="ricagent-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if container is running
check_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}Error: Container ${CONTAINER_NAME} is not running.${NC}"
        echo "Please start the container first with: docker-compose up -d"
        exit 1
    fi
}

# Function to check migration status
check_migrations() {
    echo -e "${YELLOW}Checking migration status...${NC}"
    echo "Current migration version:"
    docker exec $CONTAINER_NAME alembic current
    echo
    echo "Migration history:"
    docker exec $CONTAINER_NAME alembic history
    echo
    echo "Checking for pending changes:"
    if docker exec $CONTAINER_NAME alembic check; then
        echo -e "${GREEN}✅ No pending migrations found.${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Pending migrations detected.${NC}"
        return 1
    fi
}

# Function to generate new migration
generate_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        message="Auto-generated migration $(date +%Y%m%d_%H%M%S)"
    fi
    
    echo -e "${YELLOW}Generating new migration: $message${NC}"
    docker exec $CONTAINER_NAME alembic revision --autogenerate -m "$message"
    
    # Copy the generated migration file to host
    echo "Copying migration file to host..."
    latest_file=$(docker exec $CONTAINER_NAME ls -t /app/alembic/versions/ | head -n1)
    if [ ! -z "$latest_file" ]; then
        docker cp $CONTAINER_NAME:/app/alembic/versions/$latest_file $SCRIPT_DIR/alembic/versions/
        echo -e "${GREEN}✅ Migration file copied to host: alembic/versions/$latest_file${NC}"
    fi
}

# Function to upgrade database
upgrade_database() {
    echo -e "${YELLOW}Upgrading database to latest migration...${NC}"
    docker exec $CONTAINER_NAME alembic upgrade head
    echo -e "${GREEN}✅ Database upgrade completed.${NC}"
}

# Function to restart API container to test migrations
restart_api() {
    echo -e "${YELLOW}Restarting API container to test migration process...${NC}"
    docker restart $CONTAINER_NAME
    sleep 5
    echo -e "${GREEN}✅ Container restarted. Check logs with: docker logs $CONTAINER_NAME${NC}"
}

# Function to show help
show_help() {
    echo "RIC AI Agent - Migration Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  check                    Check current migration status"
    echo "  generate [message]       Generate new migration with optional message"
    echo "  upgrade                  Upgrade database to latest migration"
    echo "  auto                     Check, generate (if needed), and upgrade"
    echo "  restart                  Restart API container to test migrations"
    echo "  help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 generate \"Add new user fields\""
    echo "  $0 auto"
    echo "  $0 upgrade"
    echo ""
}

# Main script logic
case "${1:-help}" in
    check)
        check_container
        check_migrations
        ;;
    generate)
        check_container
        generate_migration "$2"
        ;;
    upgrade)
        check_container
        upgrade_database
        ;;
    auto)
        check_container
        echo -e "${YELLOW}Running automatic migration process...${NC}"
        if ! check_migrations; then
            echo "Generating new migration..."
            generate_migration
            echo "Applying migration..."
            upgrade_database
        fi
        echo -e "${GREEN}✅ Automatic migration process completed.${NC}"
        ;;
    restart)
        check_container
        restart_api
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac