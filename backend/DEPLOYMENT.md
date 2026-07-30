# NexusMind Deployment Report

**Version:** 1.0.0  
**Last Updated:** 2026-07-26

---

## Deployment Readiness: **95%**

The NexusMind deployment is ready for production with minimal manual configuration required.

---

## Required Secrets

| Secret | Required | Auto-Generate | Description |
|--------|----------|--------------|-------------|
| `SECRET_KEY` | Yes | Yes | JWT signing key (32+ characters) |
| `SESSION_SECRET` | Yes | Yes | Session encryption key (32+ characters) |
| `DATABASE_URL` | Yes | No | PostgreSQL connection string |
| `REDIS_URL` | Yes | No | Redis connection string |
| `CHROMADB_URL` | No | N/A | ChromaDB URL (uses local if not set) |

### Secret Generation

If `AUTO_GENERATE_SECRETS=true`, the application will automatically generate secure random keys for `SECRET_KEY` and `SESSION_SECRET` on first startup. These will be logged to stdout.

**Warning:** Auto-generated secrets are not persisted. Set them explicitly for production.

---

## Optional Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `OPENAI_API_KEY` | No | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | No | Anthropic API key for Claude models |
| `OLLAMA_BASE_URL` | No | Local Ollama instance URL |

---

## Startup Sequence

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STARTUP SEQUENCE                               │
└─────────────────────────────────────────────────────────────────────┘

1. Load Environment Variables
   ├── Load .env file (if exists)
   └── Validate required variables

2. Generate Secrets (if AUTO_GENERATE_SECRETS=true)
   ├── SECRET_KEY (32 hex characters)
   └── SESSION_SECRET (32 hex characters)

3. Create Directories
   ├── /app/workspace
   ├── /app/plugins
   ├── /app/data/chromadb
   └── /tmp/nexusmind

4. Wait for PostgreSQL
   ├── Connect to DATABASE_URL
   ├── Create database if not exists
   └── Poll every 2 seconds (60s timeout)

5. Run Alembic Migrations
   ├── Run: alembic upgrade head
   └── Skip if RUN_MIGRATIONS=false

6. Wait for Redis
   ├── Connect to REDIS_URL
   └── Poll every 2 seconds (30s timeout)

7. Wait for ChromaDB
   ├── Check HTTP health endpoint
   └── Poll every 2 seconds (60s timeout)

8. Initialize ChromaDB Collections
   ├── conversations
   ├── plans
   ├── fixes
   ├── outputs
   ├── embeddings
   ├── code
   ├── documentation
   └── tasks

9. Start FastAPI Application
   └── Initialize MCP servers

10. Application Ready
```

---

## Health Checks

### Application Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/live` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe (checks DB & Redis) |
| `/health/detailed` | GET | Detailed component status |

### Docker Health Checks

| Service | Check | Interval | Timeout | Retries |
|---------|-------|----------|--------|---------|
| `db` | `pg_isready -U postgres` | 5s | 5s | 10 |
| `redis` | `redis-cli ping` | 5s | 5s | 10 |
| `chromadb` | `curl /api/v1/heartbeat` | 10s | 5s | 10 |

---

## Service Dependencies

```
app (FastAPI)
├── db (PostgreSQL 15)
│   └── Required for: Database operations
├── redis (Redis 7)
│   └── Required for: Session cache, rate limiting
└── chromadb (ChromaDB latest)
    └── Required for: Memory/embedding storage
```

**No circular dependencies exist.**

---

## Environment Variables Reference

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Log level |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/nexusmind` | PostgreSQL connection |
| `DB_POOL_SIZE` | `20` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Max overflow connections |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `REDIS_POOL_SIZE` | `10` | Connection pool size |

### ChromaDB

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMADB_URL` | `` | Remote ChromaDB URL (empty = local) |
| `CHROMADB_PERSIST_DIRECTORY` | `./data/chromadb` | Local persist directory |
| `CHROMADB_COLLECTION_NAME` | `nexusmind_memory` | Default collection name |

### Startup

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_GENERATE_SECRETS` | `true` | Auto-generate SECRET_KEY/SESSION_SECRET |
| `RUN_MIGRATIONS` | `true` | Run Alembic migrations on startup |
| `STARTUP_DB_TIMEOUT` | `60` | PostgreSQL connection timeout (seconds) |
| `STARTUP_REDIS_TIMEOUT` | `30` | Redis connection timeout (seconds) |
| `STARTUP_CHROMADB_TIMEOUT` | `60` | ChromaDB connection timeout (seconds) |

---

## Troubleshooting

### PostgreSQL Not Available

**Error:** `PostgreSQL did not become available within X seconds`

**Solution:**
1. Verify PostgreSQL is running: `docker-compose ps db`
2. Check logs: `docker-compose logs db`
3. Verify DATABASE_URL is correct
4. Check network connectivity

### Redis Not Available

**Error:** `Redis did not become available within X seconds`

**Solution:**
1. Verify Redis is running: `docker-compose ps redis`
2. Check logs: `docker-compose logs redis`
3. Verify REDIS_URL is correct

### ChromaDB Not Available

**Error:** `ChromaDB did not become available within X seconds`

**Solution:**
1. Verify ChromaDB is running: `docker-compose ps chromadb`
2. Check logs: `docker-compose logs chromadb`
3. Check CHROMADB_URL if using remote instance

### Migration Failed

**Warning:** `Migration failed (may be OK if already up to date)`

**Solution:**
1. Check migration logs: `docker-compose logs app`
2. Run migrations manually: `docker-compose exec app alembic upgrade head`

### Secret Key Issues

**Error:** `SECRET_KEY is not set`

**Solution:**
1. Set SECRET_KEY environment variable
2. Or ensure AUTO_GENERATE_SECRETS=true

---

## Quick Start

### Development

```bash
cd nexusmind/backend
cp .env.example .env
docker-compose up --build
```

### Production

```bash
cd nexusmind/backend
cp .env.example .env
# Edit .env with production values
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Northflank Deployment

1. Copy `northflank.yaml` to your Northflank project
2. Configure secrets in Northflank dashboard:
   - `SECRET_KEY`
   - `SESSION_SECRET`
3. Run the template
4. Application will auto-initialize

---

## API Documentation

Once running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`
