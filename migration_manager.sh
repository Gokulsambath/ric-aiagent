#!/bin/bash
# =============================================================================
# RIC AI Agent - Comprehensive Migration Management System
# =============================================================================
# This script provides a complete migration management solution that prevents
# common issues like missing revisions, broken chains, and filename problems.
#
# Usage: ./migration_manager.sh [command] [options]
# =============================================================================

set -e

# Configuration
CONTAINER_NAME="ricagent-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAX_MIGRATION_NAME_LENGTH=40

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

validate_migration_name() {
    local name="$1"
    
    if [ -z "$name" ]; then
        log_error "Migration name cannot be empty"
        return 1
    fi
    
    if [ ${#name} -gt $MAX_MIGRATION_NAME_LENGTH ]; then
        log_error "Migration name too long (${#name} chars, max $MAX_MIGRATION_NAME_LENGTH)"
        log_warn "Suggested name: ${name:0:35}"
        return 1
    fi
    
    if [[ ! "$name" =~ ^[a-zA-Z][a-zA-Z0-9_]*$ ]]; then
        log_error "Migration name must start with a letter and contain only letters, numbers, and underscores"
        return 1
    fi
    
    return 0
}

check_docker_environment() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    return 0
}

check_container_status() {
    local status=$(docker-compose ps -q ricagent-api 2>/dev/null)
    if [ -z "$status" ]; then
        log_warn "API container is not running"
        return 1
    fi
    
    local health=$(docker inspect --format='{{.State.Health.Status}}' ricagent-api 2>/dev/null || echo "unknown")
    if [ "$health" = "unhealthy" ]; then
        log_warn "API container is unhealthy"
        return 2
    fi
    
    return 0
}

# =============================================================================
# MIGRATION REPAIR FUNCTIONS
# =============================================================================

get_db_migration_version() {
    docker-compose exec -T postgres psql -U ricagoapi_user -d ricagoapi -t -c \
        "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null | tr -d ' \n' || echo "none"
}

get_latest_migration_file() {
    ls -1 alembic/versions/*.py 2>/dev/null | sort | tail -1 | xargs basename 2>/dev/null | cut -d'_' -f1 || echo "none"
}

repair_migration_state() {
    log_warn "Detecting migration state mismatch..."
    
    local db_version=$(get_db_migration_version)
    local latest_file=$(get_latest_migration_file)
    
    log_info "Database migration version: $db_version"
    log_info "Latest migration file: $latest_file"
    
    # Check if database version exists in files
    if [ "$db_version" != "none" ] && [ ! -f "alembic/versions/${db_version}"* ]; then
        log_warn "Database has migration $db_version but file doesn't exist"
        
        if [ "$latest_file" != "none" ]; then
            log_info "Updating database to match latest file: $latest_file"
            docker-compose exec -T postgres psql -U ricagoapi_user -d ricagoapi -c \
                "UPDATE alembic_version SET version_num = '$latest_file';" 2>/dev/null
            log_success "Migration state synchronized"
        else
            log_error "No migration files found"
            return 1
        fi
    fi
    
    return 0
}

validate_migration_chain() {
    log_info "Validating migration chain integrity..."
    
    if docker-compose run --rm ricagent-api alembic check >/dev/null 2>&1; then
        log_success "Migration chain is valid"
        return 0
    else
        log_warn "Migration chain validation failed"
        return 1
    fi
}

# =============================================================================
# CORE MIGRATION FUNCTIONS
# =============================================================================

show_migration_status() {
    log_info "Current migration status:"
    echo
    
    echo "Database Migration Version:"
    local db_version=$(get_db_migration_version)
    echo "  $db_version"
    echo
    
    echo "Current Alembic State:"
    docker-compose run --rm ricagent-api alembic current 2>/dev/null || echo "  Unable to determine current state"
    echo
    
    echo "Migration History:"
    docker-compose run --rm ricagent-api alembic history 2>/dev/null || echo "  Unable to retrieve history"
    echo
    
    echo "Available Migration Files:"
    if ls alembic/versions/*.py >/dev/null 2>&1; then
        ls -1 alembic/versions/*.py | sort | while read file; do
            basename "$file" | sed 's/^/  /'
        done
    else
        echo "  No migration files found"
    fi
}

create_migration() {
    local message="$1"
    local auto_generate="${2:-true}"
    
    if [ -z "$message" ]; then
        read -p "Enter migration message: " message
    fi
    
    if ! validate_migration_name "$message"; then
        return 1
    fi
    
    log_info "Creating migration: $message"
    
    local cmd="alembic revision --message \"$message\""
    if [ "$auto_generate" = "true" ]; then
        cmd="$cmd --autogenerate"
        log_info "Auto-generating migration based on model changes..."
    else
        log_info "Creating empty migration template..."
    fi
    
    if docker-compose run --rm ricagent-api $cmd; then
        log_success "Migration created successfully"
        log_warn "Remember to rebuild the container: docker-compose build ricagent-api"
        return 0
    else
        log_error "Failed to create migration"
        return 1
    fi
}

apply_migrations() {
    log_info "Applying database migrations..."
    
    # Check and repair migration state if needed
    if ! validate_migration_chain; then
        if ! repair_migration_state; then
            log_error "Failed to repair migration state"
            return 1
        fi
        
        if ! validate_migration_chain; then
            log_error "Migration chain still invalid after repair"
            return 1
        fi
    fi
    
    # Apply migrations
    if docker-compose run --rm ricagent-api alembic upgrade head; then
        log_success "Migrations applied successfully"
        return 0
    else
        log_error "Migration failed"
        return 1
    fi
}

rollback_migration() {
    local target="${1:-1}"
    log_warn "Rolling back $target migration(s)..."
    
    if docker-compose run --rm ricagent-api alembic downgrade -$target; then
        log_success "Rollback completed"
    else
        log_error "Rollback failed"
        return 1
    fi
}

rebuild_and_restart() {
    log_info "Rebuilding and restarting API container..."
    
    docker-compose build ricagent-api
    docker-compose restart ricagent-api
    
    # Wait for container to be healthy
    log_info "Waiting for container to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if check_container_status >/dev/null 2>&1; then
            log_success "Container is healthy"
            return 0
        fi
        sleep 2
        ((attempt++))
    done
    
    log_error "Container failed to become healthy"
    return 1
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

cleanup_old_migrations() {
    log_info "Cleaning up orphaned migration files..."
    
    # Find migration files that are not in the migration chain
    local valid_migrations=$(docker-compose run --rm ricagent-api alembic history 2>/dev/null | grep "Rev:" | awk '{print $2}' || echo "")
    
    for file in alembic/versions/*.py; do
        if [ -f "$file" ]; then
            local rev=$(basename "$file" | cut -d'_' -f1)
            if [[ "$valid_migrations" != *"$rev"* ]]; then
                log_warn "Found orphaned migration file: $file"
                read -p "Remove this file? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm "$file"
                    log_info "Removed $file"
                fi
            fi
        fi
    done
}

show_help() {
    cat << EOF
RIC AI Agent - Migration Management System
==========================================

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  status                 Show current migration status
  create [name]          Create new migration (prompts for name if not provided)
  create-empty [name]    Create empty migration template
  apply                  Apply all pending migrations
  rollback [count]       Rollback migrations (default: 1)
  rebuild                Rebuild container and restart
  cleanup                Remove orphaned migration files
  repair                 Repair broken migration state
  validate               Validate migration chain
  help                   Show this help message

Examples:
  $0 status
  $0 create add_user_preferences
  $0 create-empty custom_migration
  $0 apply
  $0 rollback 2
  $0 rebuild

Safety Features:
  - Migration name validation (length and format)
  - Automatic migration state repair
  - Chain integrity validation
  - Container health monitoring
  - Orphaned file detection

EOF
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    # Pre-flight checks
    if ! check_docker_environment; then
        exit 1
    fi
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Parse command
    case "${1:-help}" in
        "status"|"st")
            show_migration_status
            ;;
        "create"|"c")
            create_migration "$2" "true"
            ;;
        "create-empty"|"ce")
            create_migration "$2" "false"
            ;;
        "apply"|"up")
            apply_migrations
            ;;
        "rollback"|"down")
            rollback_migration "$2"
            ;;
        "rebuild"|"rb")
            rebuild_and_restart
            ;;
        "cleanup"|"clean")
            cleanup_old_migrations
            ;;
        "repair"|"fix")
            repair_migration_state
            ;;
        "validate"|"check")
            validate_migration_chain
            ;;
        "help"|"h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"