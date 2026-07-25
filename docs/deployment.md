# NexusMind Deployment Guide

This guide covers deploying NexusMind to production using Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Domain name (for HTTPS)
- SSL certificates (for HTTPS)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/nexusmind.git
cd nexusmind/deployment
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.production.example .env
nano .env  # Edit with your values
```

Required configuration:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_PASSWORD`: Strong database password
- `CORS_ORIGINS`: Your production domain

### 3. Launch Services

Start all services:
```bash
docker-compose up -d
```

Start with monitoring (Prometheus + Grafana):
```bash
docker-compose --profile monitoring up -d
```

Start with Ollama (local LLM):
```bash
docker-compose --profile with-ollama up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx                                 │
│                   (Reverse Proxy)                            │
└─────────────────────────────────────────────────────────────┘
                    │                      │
                    ▼                      ▼
┌─────────────────────────┐  ┌─────────────────────────────┐
│       Frontend           │  │        Backend               │
│    (Next.js)            │  │      (FastAPI)              │
│    Port 3000            │  │      Port 8000              │
└─────────────────────────┘  └─────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────┐
         │                             │                         │
         ▼                             ▼                         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐
│   PostgreSQL    │  │     Redis       │  │      ChromaDB          │
│   Port 5432    │  │   Port 6379     │  │      Port 8001         │
└─────────────────┘  └─────────────────┘  └─────────────────────────┘
```

## Services

### Backend
- **Image**: Custom build from `nexusmind/backend/Dockerfile`
- **Port**: 8000 (internal only, via Nginx)
- **Health**: `/health` endpoint
- **Metrics**: `/metrics` endpoint

### Frontend
- **Image**: Custom build from `nexusmind/frontend/Dockerfile`
- **Port**: 3000 (internal only, via Nginx)
- **Health**: `/health` endpoint

### Nginx
- **Image**: `nginx:1.25-alpine`
- **Ports**: 80, 443
- **Config**: `deployment/nginx/nginx.conf`

### PostgreSQL
- **Image**: `postgres:15-alpine`
- **Port**: 5432
- **Volume**: `postgres-data`

### Redis
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Volume**: `redis-data`

### ChromaDB
- **Image**: `chromadb/chroma:0.4.22`
- **Port**: 8001
- **Volume**: `chromadb-data`

## HTTPS Configuration

### Option 1: Let's Encrypt (Recommended)

1. Install certbot:
```bash
apt install certbot python3-certbot-nginx
```

2. Obtain certificate:
```bash
certbot --nginx -d your-domain.com -d app.your-domain.com
```

3. Uncomment HTTPS server block in `nginx.conf`

### Option 2: Self-Signed / Existing Certificates

1. Place certificates in `deployment/nginx/ssl/`:
```
deployment/nginx/ssl/
├── cert.pem
└── key.pem
```

2. Uncomment HTTPS server block in `nginx.conf`

## Resource Limits

The Docker Compose file includes resource limits:

| Service | CPU Limit | Memory Limit |
|---------|----------|--------------|
| backend | 2 cores | 2 GB |
| frontend | 1 core | 512 MB |
| db | 1 core | 1 GB |
| redis | 0.5 cores | 256 MB |
| chromadb | 1 core | 1 GB |
| ollama | 4 cores | 8 GB |

Adjust these based on your hardware.

## Monitoring Stack

Enable Prometheus + Grafana:

```bash
docker-compose --profile monitoring up -d
```

Access:
- Prometheus: http://your-domain.com:9090
- Grafana: http://your-domain.com:3001

Default credentials: `admin` / `admin` (change in `.env`)

## Database Migrations

Run migrations on startup (handled automatically) or manually:

```bash
docker-compose exec backend alembic upgrade head
```

## Backup

### PostgreSQL

```bash
docker-compose exec db pg_dump -U postgres nexusmind > backup.sql
```

### Redis

```bash
docker-compose exec redis redis-cli SAVE
docker cp nexusmind-redis:/data/dump.rdb ./redis-backup.rdb
```

## Scaling

### Horizontal Scaling (Backend)

For multiple backend instances:

1. Update `docker-compose.yml`:
```yaml
backend:
  deploy:
    replicas: 3
```

2. Use a shared session store (Redis is already configured)

3. Ensure sticky sessions are enabled in Nginx (optional)

### Database Connection Pooling

Increase pool size in `.env`:
```
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20
```

## Troubleshooting

### Check Service Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### Check Service Health

```bash
curl http://localhost:8000/health
curl http://localhost:3000/health
curl http://localhost:8001/health  # ChromaDB
```

### Restart a Service

```bash
docker-compose restart backend
```

### Rebuild After Code Changes

```bash
docker-compose build backend frontend
docker-compose up -d
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` properly
- [ ] Enable HTTPS
- [ ] Set appropriate resource limits
- [ ] Enable firewall (only ports 80, 443)
- [ ] Regular backups
- [ ] Update Docker images regularly

## Update Procedure

1. Pull latest code:
```bash
git pull origin main
```

2. Rebuild images:
```bash
docker-compose build backend frontend
```

3. Restart services:
```bash
docker-compose up -d
```

4. Run migrations if needed:
```bash
docker-compose exec backend alembic upgrade head
```
