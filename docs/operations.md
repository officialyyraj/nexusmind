# NexusMind Operations Guide

This guide covers operational procedures for running NexusMind in production.

## Common Operations

### Starting the Application

```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start specific services
docker-compose up -d backend redis
```

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (full cleanup)
docker-compose down -v
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend

# Restart with rebuild
docker-compose restart --build backend
```

## Monitoring

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail 100 backend
```

### Check Resource Usage

```bash
docker stats
```

### Access Container Shell

```bash
docker-compose exec backend /bin/sh
docker-compose exec db psql -U postgres
```

## Database Operations

### Run Migrations

```bash
# Apply migrations
docker-compose exec backend alembic upgrade head

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add users table"

# Rollback
docker-compose exec backend alembic downgrade -1
```

### Database Shell

```bash
docker-compose exec db psql -U nexusmind nexusmind
```

### Backup Database

```bash
# Create backup
docker-compose exec db pg_dump -U postgres nexusmind > backup_$(date +%Y%m%d).sql

# Restore from backup
cat backup_20240115.sql | docker-compose exec -T db psql -U postgres nexusmind
```

## Cache Operations

### Redis CLI

```bash
docker-compose exec redis redis-cli
```

### Common Redis Commands

```
# Check connection
PING

# View keys
KEYS *

# View memory usage
INFO memory

# Flush all keys (careful!)
FLUSHALL
```

### Clear Session Cache

```bash
docker-compose exec redis redis-cli FLUSHDB
```

## Agent Operations

### View Active Sessions

```bash
curl http://localhost:8000/api/v1/sessions
```

### Cancel Running Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions/{session_id}/cancel
```

### View Session Logs

```bash
curl http://localhost:8000/api/v1/sessions/{session_id}/logs
```

## Docker Operations

### Rebuild Images

```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild specific service
docker-compose build backend
```

### Cleanup

```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Full cleanup (careful!)
docker system prune -af
```

### Update Images

```bash
# Pull latest
docker-compose pull

# Rebuild with latest
docker-compose pull && docker-compose up -d
```

## Configuration

### Update Environment Variables

1. Edit `.env` file
2. Restart affected services:
```bash
docker-compose up -d backend
```

### Hot Reload Settings

Some settings support hot reload. Check endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/admin/reload-config
```

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
docker-compose logs backend
```

2. Check port conflicts:
```bash
netstat -tlnp | grep -E '8000|3000|5432|6379'
```

3. Check volume permissions:
```bash
ls -la ./data
```

### High Memory Usage

1. Check container memory:
```bash
docker stats --no-stream
```

2. Reduce memory limits in `docker-compose.yml`

3. Restart services:
```bash
docker-compose restart
```

### Database Connection Issues

1. Check database health:
```bash
curl http://localhost:8000/health/detailed | jq '.components[] | select(.name == "database")'
```

2. Check database logs:
```bash
docker-compose logs db
```

3. Verify connection string in `.env`

### Slow API Responses

1. Check Prometheus metrics:
```bash
curl http://localhost:9090/api/v1/query?query=nexusmind_request_duration_seconds
```

2. Check database queries:
```bash
docker-compose exec db psql -U nexusmind -c "SELECT * FROM pg_stat_activity;"
```

3. Check Redis memory:
```bash
docker-compose exec redis redis-cli INFO memory
```

## Maintenance

### Regular Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Backup database | Daily | `pg_dump` |
| Rotate logs | Weekly | `logrotate` |
| Update images | Weekly | `docker-compose pull` |
| Clean unused resources | Monthly | `docker system prune` |

### Log Rotation

Create `/etc/logrotate.d/nexusmind`:

```
/var/lib/docker/containers/*/*-json.log {
    rotate 7
    daily
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### Database Maintenance

```bash
# Analyze tables
docker-compose exec db psql -U nexusmind -c "ANALYZE;"

# Vacuum tables
docker-compose exec db psql -U nexusmind -c "VACUUM ANALYZE;"

# Check index usage
docker-compose exec db psql -U nexusmind -c "SELECT * FROM pg_stat_user_indexes;"
```

## Security

### Update Secrets

1. Generate new secret:
```bash
openssl rand -hex 32
```

2. Update `.env`:
```
SECRET_KEY=new-secret-value
```

3. Restart services:
```bash
docker-compose up -d
```

### Rotate API Keys

```bash
# Create new key
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer $OLD_TOKEN" \
  -d '{"name": "New Key"}'

# Revoke old key
curl -X DELETE http://localhost:8000/api/v1/auth/api-keys/{old_key_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Check Failed Login Attempts

```bash
curl http://localhost:8000/api/v1/admin/security/failed-logins
```

## Scaling

### Horizontal Scaling

To scale backend:
```bash
docker-compose up -d --scale backend=3
```

Update Nginx upstream configuration to match.

### Load Balancing

Nginx automatically load balances to multiple backend instances.

### Database Connection Pool

Adjust in `.env`:
```
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20
```

## Disaster Recovery

### Full Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/nexusmind"

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U postgres nexusmind > $BACKUP_DIR/db_$DATE.sql

# Redis backup
docker-compose exec redis redis-cli BGSAVE
sleep 5
docker cp nexusmind-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Config backup
cp .env $BACKUP_DIR/env_$DATE

echo "Backup complete: $BACKUP_DIR"
```

### Restore from Backup

```bash
# Restore database
cat backups/nexusmind/db_20240115.sql | docker-compose exec -T db psql -U postgres nexusmind

# Restore Redis
docker cp backups/nexusmind/redis_20240115.rdb nexusmind-redis:/data/dump.rdb
docker-compose exec redis redis-cli CONFIG SET appendonly no
docker-compose exec redis redis-cli DEBUG RELOAD
```

## Performance Optimization

### Backend Performance

1. Increase worker count:
```bash
docker-compose exec backend uvicorn app.main:app --workers 4
```

2. Enable response caching in Redis

3. Optimize database queries

### Frontend Performance

1. Enable Next.js caching

2. Configure CDN for static assets

3. Optimize images

### Database Performance

1. Add indexes for common queries

2. Enable query caching

3. Consider read replicas

## Alert Response

### High CPU Alert

1. Identify processes:
```bash
docker-compose top backend
```

2. Check for runaway queries:
```bash
docker-compose exec db psql -U nexusmind -c "SELECT pid, query, state FROM pg_stat_activity;"
```

3. Restart if needed:
```bash
docker-compose restart backend
```

### Memory Alert

1. Check memory usage:
```bash
docker stats --no-stream
```

2. Increase limits or scale down

3. Restart affected service

### Disk Full Alert

1. Check disk usage:
```bash
df -h
```

2. Clean up logs:
```bash
docker-compose logs --tail 0 > /dev/null  # Truncate
rm -rf /var/lib/docker/containers/*/logs
```

3. Clean up old backups
