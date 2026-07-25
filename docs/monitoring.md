# NexusMind Monitoring Guide

This guide covers monitoring and observability for NexusMind.

## Overview

NexusMind includes comprehensive monitoring with:

- **Prometheus Metrics**: Request counts, latencies, errors
- **OpenTelemetry**: Distributed tracing
- **Structured Logging**: JSON logs with context
- **Health Checks**: Component status monitoring

## Endpoints

### Health Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Basic health check |
| `GET /health/detailed` | Detailed component status |
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Kubernetes readiness probe |

### Metrics Endpoint

| Endpoint | Description |
|----------|-------------|
| `GET /metrics` | Prometheus metrics (text format) |

## Metrics

### HTTP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_requests_total` | Counter | method, endpoint, status | Total requests |
| `nexusmind_request_duration_seconds` | Histogram | method, endpoint | Request latency |
| `nexusmind_errors_total` | Counter | type, endpoint | Error count |

### Session Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `nexusmind_active_sessions` | Gauge | Active sessions count |
| `nexusmind_sessions_total` | Counter | Total sessions created |

### Agent Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_active_agents` | Gauge | - | Active agents count |
| `nexusmind_agents_executed_total` | Counter | agent_type, status | Total executions |
| `nexusmind_agent_execution_duration_seconds` | Histogram | agent_type | Execution time |

### Tool Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_tool_executions_total` | Counter | tool_name, status | Total executions |
| `nexusmind_tool_execution_duration_seconds` | Histogram | tool_name | Execution time |

### Database Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_db_queries_total` | Counter | operation, status | Total queries |
| `nexusmind_db_query_duration_seconds` | Histogram | operation | Query latency |

### WebSocket Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `nexusmind_websocket_connections` | Gauge | Active connections |
| `nexusmind_websocket_messages_total` | Counter | Messages sent/received |

### MCP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_mcp_tool_invocations_total` | Counter | server, tool, status | Total invocations |
| `nexusmind_mcp_latency_seconds` | Histogram | server, tool | Invocation latency |

### Browser Automation Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_browser_actions_total` | Counter | action_type, status | Total actions |
| `nexusmind_browser_action_duration_seconds` | Histogram | action_type | Action time |

### Docker Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_docker_containers` | Gauge | status | Container counts |

### Resource Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_memory_usage_bytes` | Gauge | type | Memory usage |
| `nexusmind_cpu_usage_percent` | Gauge | - | CPU usage |

### Token Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nexusmind_tokens_used_total` | Counter | model, type | Tokens used |

## Prometheus Configuration

The included `prometheus.yml` scrapes:

- NexusMind backend at `/metrics`
- Prometheus self-monitoring

Add additional scrape targets as needed:

```yaml
scrape_configs:
  - job_name: 'nexusmind-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
```

## Grafana Dashboards

### Pre-configured Dashboards

1. **NexusMind Overview**: High-level metrics
2. **API Performance**: Latency, throughput, errors
3. **Agent Execution**: Agent metrics and timing
4. **System Health**: Resource usage, Docker status

### Import Dashboards

1. Access Grafana at `http://your-domain.com:3001`
2. Go to Dashboards → Import
3. Upload JSON dashboard file

## Alerting

### Example Alert Rules

Create `prometheus/alerts.yml`:

```yaml
groups:
  - name: nexusmind
    rules:
      - alert: HighErrorRate
        expr: rate(nexusmind_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(nexusmind_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency"

      - alert: ServiceDown
        expr: up{job="nexusmind-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend service is down"
```

## Structured Logging

Logs include contextual information:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.api.agents",
  "message": "Agent executed successfully",
  "request_id": "abc-123-def",
  "session_id": "sess-456",
  "agent_id": "agent-789",
  "user_id": "user-001",
  "duration_ms": 1500
}
```

### Log Fields

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp |
| `level` | Log level |
| `logger` | Logger name |
| `message` | Log message |
| `request_id` | HTTP request ID |
| `session_id` | Session ID (if applicable) |
| `workflow_id` | Workflow ID (if applicable) |
| `agent_id` | Agent ID (if applicable) |
| `user_id` | User ID (if applicable) |
| `duration_ms` | Operation duration |

## Health Check Details

The `/health/detailed` endpoint reports on:

| Component | Check |
|----------|-------|
| `database` | PostgreSQL connectivity |
| `redis` | Redis ping |
| `chromadb` | ChromaDB heartbeat |
| `ollama` | Ollama API |
| `mcp_servers` | MCP server status |
| `docker` | Docker connectivity |
| `browser_service` | Playwright availability |

### Example Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "components": [
    {
      "name": "database",
      "status": "healthy",
      "latency_ms": 5.2,
      "message": "Database connection successful"
    },
    {
      "name": "redis",
      "status": "healthy",
      "latency_ms": 1.1,
      "message": "Redis connection successful"
    }
  ]
}
```

## Distributed Tracing

OpenTelemetry traces include:

- Request spans with HTTP context
- Database query spans
- Tool execution spans
- Agent execution spans
- MCP invocation spans

### Trace Context

Context is propagated via:

- HTTP headers (`traceparent`, `tracestate`)
- WebSocket messages
- Internal async tasks

## Grafana Setup

### Add Prometheus Datasource

1. Go to Configuration → Data Sources
2. Add Prometheus
3. URL: `http://prometheus:9090`

### Create Dashboard

Example queries:

```
# Request rate
rate(nexusmind_requests_total[5m])

# Error rate
rate(nexusmind_errors_total[5m])

# P95 latency
histogram_quantile(0.95, rate(nexusmind_request_duration_seconds_bucket[5m]))

# Active sessions
nexusmind_active_sessions
```

## Performance Tuning

### Increase Scrape Interval

In `prometheus.yml`:

```yaml
scrape_interval: 30s  # Default is 15s
```

### Adjust Histogram Buckets

Modify buckets in `app/monitoring/metrics.py` based on expected latency ranges.

### Resource Monitoring

Enable cAdvisor for container metrics:

```yaml
cadvisor:
  image: gcr.io/cadvisor/cadvisor:v0.47.0
  volumes:
    - /:/rootfs:ro
    - /var/run:/var/run:ro
```
