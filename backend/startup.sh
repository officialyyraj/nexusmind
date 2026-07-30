#!/bin/bash
# =============================================================================
# NexusMind Zero-Touch Startup Script
# =============================================================================
# This script initializes the NexusMind application before running.
# It handles:
#   - Environment validation
#   - Secret generation
#   - Directory creation
#   - Dependency health checks
#   - Database migrations
#   - Application startup
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "  ${1}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_ok() {
    echo -e "${GREEN}✓${NC} ${1}"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} ${1}"
}

print_error() {
    echo -e "${RED}✗${NC} ${1}"
}

# Check environment
print_step "Checking Environment"

# Load .env file if it exists
if [ -f ".env" ]; then
    print_ok "Loading environment from .env"
    set -a
    source .env
    set +a
else
    print_warn "No .env file found, using defaults"
fi

# Check required environment variables
ERRORS=0

if [ -z "$DATABASE_URL" ]; then
    print_error "DATABASE_URL is not set"
    ERRORS=$((ERRORS + 1))
else
    print_ok "DATABASE_URL is configured"
fi

if [ -z "$REDIS_URL" ]; then
    print_error "REDIS_URL is not set"
    ERRORS=$((ERRORS + 1))
else
    print_ok "REDIS_URL is configured"
fi

if [ $ERRORS -gt 0 ]; then
    print_error "Missing required environment variables"
    exit 1
fi

# Generate secrets if needed
print_step "Checking Secrets"

if [ -z "$SECRET_KEY" ]; then
    if [ "$AUTO_GENERATE_SECRETS" != "false" ]; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        export SECRET_KEY
        print_ok "Generated SECRET_KEY"
    else
        print_error "SECRET_KEY is not set"
        exit 1
    fi
else
    print_ok "SECRET_KEY is configured"
fi

if [ -z "$SESSION_SECRET" ]; then
    if [ "$AUTO_GENERATE_SECRETS" != "false" ]; then
        SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        export SESSION_SECRET
        print_ok "Generated SESSION_SECRET"
    else
        print_error "SESSION_SECRET is not set"
        exit 1
    fi
else
    print_ok "SESSION_SECRET is configured"
fi

# Create directories
print_step "Creating Directories"

mkdir -p workspace
mkdir -p plugins
mkdir -p data/chromadb
mkdir -p /tmp/nexusmind

print_ok "workspace/"
print_ok "plugins/"
print_ok "data/chromadb/"
print_ok "/tmp/nexusmind/"

# Wait for dependencies
print_step "Waiting for Dependencies"

WAIT_TIMEOUT=${STARTUP_DB_TIMEOUT:-60}
POLL_INTERVAL=2

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
if [ -n "$DATABASE_URL" ]; then
    python3 -c "
import asyncio
import asyncpg
from urllib.parse import urlparse

async def wait():
    url = '$DATABASE_URL'
    parsed = urlparse(url.replace('postgresql://', 'http://').replace('postgres://', 'http://'))
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    db = parsed.path.lstrip('/') if parsed.path else 'nexusmind'
    
    for i in range($WAIT_TIMEOUT // $POLL_INTERVAL):
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=parsed.username or 'postgres',
                password=parsed.password or 'postgres',
                timeout=5,
            )
            await conn.close()
            print('PostgreSQL is ready!')
            return True
        except Exception as e:
            print(f'Waiting... ({i * $POLL_INTERVAL}s)')
            await asyncio.sleep($POLL_INTERVAL)
    print('ERROR: PostgreSQL not available')
    return False

result = asyncio.run(wait())
exit(0 if result else 1)
" && print_ok "PostgreSQL is ready" || { print_error "PostgreSQL not available"; exit 1; }
fi

# Wait for Redis
echo "Waiting for Redis..."
python3 -c "
import asyncio
import redis.asyncio as redis
from urllib.parse import urlparse

async def wait():
    url = '$REDIS_URL'
    parsed = urlparse(url.replace('redis://', 'http://'))
    host = parsed.hostname or 'localhost'
    port = parsed.port or 6379
    db = parsed.path.lstrip('/') if parsed.path else '0'
    
    for i in range(30 // 2):
        try:
            client = redis.Redis(host=host, port=port, db=int(db) if db.isdigit() else 0)
            await client.ping()
            await client.aclose()
            print('Redis is ready!')
            return True
        except Exception as e:
            print(f'Waiting... ({i * 2}s)')
            await asyncio.sleep(2)
    print('ERROR: Redis not available')
    return False

result = asyncio.run(wait())
exit(0 if result else 1)
" && print_ok "Redis is ready" || { print_error "Redis not available"; exit 1; }

# Run migrations
print_step "Running Database Migrations"

if [ "$RUN_MIGRATIONS" != "false" ]; then
    python3 -m alembic upgrade head && print_ok "Migrations completed" || { print_warn "Migration failed (may be OK if already up to date)"; }
else
    print_warn "Migrations skipped (RUN_MIGRATIONS=false)"
fi

# Print diagnostic report
print_step "Environment Diagnostic Report"
python3 -c "
import os
from pathlib import Path

print('REQUIRED SECRETS:')
print('-' * 40)
print(f\"  SECRET_KEY:       {'✓ Configured' if os.environ.get('SECRET_KEY') else '✗ Missing'}\")
print(f\"  SESSION_SECRET:   {'✓ Configured' if os.environ.get('SESSION_SECRET') else '✗ Missing'}\")
print()
print('DATABASE:')
print('-' * 40)
print(f\"  DATABASE_URL:     {'✓ Configured' if os.environ.get('DATABASE_URL') else '✗ Missing'}\")
print()
print('REDIS:')
print('-' * 40)
print(f\"  REDIS_URL:       {'✓ Configured' if os.environ.get('REDIS_URL') else '✗ Missing'}\")
print()
print('DIRECTORIES:')
print('-' * 40)
for d in ['workspace', 'plugins', 'data/chromadb']:
    p = Path(d)
    print(f\"  {'✓' if p.exists() else '✗'} {d}/\")
"

# Start the application
print_step "Starting NexusMind"

exec "$@"
