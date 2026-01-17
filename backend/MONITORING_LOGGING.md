# Monitoring and Logging Implementation

This document describes the comprehensive monitoring and logging system implemented for the SVA-Chatbot.

## Overview

Task 34 implements a production-ready monitoring and logging system with three key components:

1. Structured logging in JSON format
2. Performance metrics tracking
3. Comprehensive health check endpoints

## 1. Structured Logging (Task 34.1)

### Implementation

Created `app/utils/structured_logging.py` with comprehensive structured logging capabilities.

### Features

**JSON Format Logging:**

- All logs output in JSON format for easy parsing and analysis
- Includes timestamp, level, logger name, message, module, function, and line number
- Automatic exception tracking with full stack traces
- Request ID tracking for request correlation

**Structured Logger Class:**

- Wrapper for standard Python logging with context support
- Methods: `debug()`, `info()`, `warning()`, `error()`, `critical()`, `exception()`
- Supports additional structured data via kwargs

**Specialized Logging Functions:**

- `log_api_request()` - Log API requests with method, path, status, duration
- `log_agent_execution()` - Log agent executions with status and duration
- `log_error()` - Log errors with full context and stack traces
- `log_database_operation()` - Log database operations
- `log_llm_request()` - Log LLM API requests with token usage

**Request Tracking:**

- Automatic request ID generation and tracking
- Request ID included in all logs during request processing
- Request ID returned in response headers (`X-Request-ID`)

### Usage Examples

```python
from app.utils.structured_logging import StructuredLogger, log_api_request

# Using structured logger
logger = StructuredLogger("my_module")
logger.info("Processing started", user_id="123", project_id="456")

# Logging API requests
log_api_request(
    method="GET",
    path="/api/projects",
    status_code=200,
    duration=0.123,
    user_id="user123"
)

# Logging errors with context
log_error(
    error_type="ValidationError",
    error_message="Invalid input",
    context={"field": "email", "value": "invalid"}
)
```

### Log Format

Example JSON log entry:

```json
{
  "timestamp": "2026-01-16T18:00:00.123456",
  "level": "INFO",
  "logger": "api",
  "message": "API Request: GET /api/projects",
  "module": "main",
  "function": "log_requests",
  "line": 123,
  "request_id": "uuid-here",
  "event_type": "api_request",
  "method": "GET",
  "path": "/api/projects",
  "status_code": 200,
  "duration_seconds": 0.123
}
```

### Integration

- Integrated into FastAPI middleware for automatic request logging
- Integrated into agent base class for agent execution logging
- Used throughout the application for consistent logging

### Benefits

- **Easy parsing**: JSON format enables easy log analysis with tools like ELK, Splunk
- **Structured queries**: Search logs by specific fields (request_id, user_id, etc.)
- **Request tracing**: Track requests across the system using request IDs
- **Error debugging**: Full context and stack traces for all errors

## 2. Performance Metrics Tracking (Task 34.2)

### Implementation

Created `app/utils/metrics.py` with comprehensive performance metrics tracking.

### Features

**Metrics Categories:**

- **API Metrics**: Track response times for all API endpoints
- **Agent Metrics**: Track execution times for all agents
- **Database Metrics**: Track query times for database operations
- **LLM Metrics**: Track latency for LLM API requests

**Statistical Analysis:**

- Count, min, max, mean, median
- 95th percentile (p95) and 99th percentile (p99)
- Automatic calculation for all metrics

**Metrics Timer:**

- Context manager for easy timing of operations
- Automatic duration calculation

**Automatic Cleanup:**

- Configurable retention period (default: 24 hours)
- Automatic removal of old metrics

### Usage Examples

```python
from app.utils.metrics import (
    track_api_request,
    track_agent_execution,
    track_database_query,
    track_llm_request,
    MetricsTimer,
    get_all_metrics
)

# Track API request
track_api_request("GET", "/api/projects", duration=0.123)

# Track agent execution
track_agent_execution("SpecParser", duration=1.234)

# Track database query
track_database_query("find", "projects", duration=0.045)

# Track LLM request
track_llm_request("llama-3.3-70b-versatile", duration=3.456)

# Use metrics timer
with MetricsTimer() as timer:
    # Do work
    pass
duration = timer.duration

# Get all metrics
metrics = get_all_metrics()
```

### Metrics Endpoint

Access metrics via `/metrics` endpoint:

```json
{
  "metrics": {
    "api": {
      "GET:/api/projects": {
        "count": 150,
        "min": 0.045,
        "max": 0.234,
        "mean": 0.123,
        "median": 0.118,
        "p95": 0.189,
        "p99": 0.215
      }
    },
    "agents": {
      "SpecParser": {
        "count": 25,
        "min": 0.8,
        "max": 3.2,
        "mean": 1.5,
        "median": 1.4,
        "p95": 2.8,
        "p99": 3.0
      }
    },
    "database": {
      "find:projects": {
        "count": 200,
        "min": 0.012,
        "max": 0.089,
        "mean": 0.034,
        "median": 0.031,
        "p95": 0.067,
        "p99": 0.078
      }
    },
    "llm": {
      "llama-3.3-70b-versatile": {
        "count": 50,
        "min": 1.2,
        "max": 5.6,
        "mean": 2.8,
        "median": 2.5,
        "p95": 4.8,
        "p99": 5.2
      }
    }
  }
}
```

### Integration

- Integrated into FastAPI middleware for automatic API tracking
- Integrated into Groq client for LLM request tracking
- Ready for integration into database operations
- Used in agent base class for agent execution tracking

### Benefits

- **Performance monitoring**: Track response times across all components
- **Bottleneck identification**: Identify slow operations with p95/p99 metrics
- **Capacity planning**: Understand system load and performance trends
- **SLA monitoring**: Ensure response times meet requirements

## 3. Health Check Endpoints (Task 34.3)

### Implementation

Enhanced health check endpoints in `app/main.py` with comprehensive component checks.

### Endpoints

#### `/health` - Comprehensive Health Check

Checks all system components and returns detailed status:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-16T18:00:00.123456",
  "components": {
    "database": {
      "status": "healthy",
      "message": "Connected"
    },
    "llm_api": {
      "status": "healthy",
      "message": "Available",
      "primary_model": "llama-3.3-70b-versatile",
      "fallback_model": "mixtral-8x7b-32768"
    },
    "job_queue": {
      "status": "healthy",
      "message": "Running",
      "workers": 5,
      "queue_size": 3
    }
  }
}
```

**Status Values:**

- `healthy`: All components operational
- `degraded`: Some non-critical components have issues
- `unhealthy`: Critical components are down

#### `/health/live` - Liveness Probe

Simple endpoint for Kubernetes liveness checks:

```json
{
  "status": "alive"
}
```

Returns 200 if the application process is running.

#### `/health/ready` - Readiness Probe

Endpoint for Kubernetes readiness checks:

```json
{
  "status": "ready"
}
```

Returns 200 if the application is ready to serve traffic (database connected).
Returns 503 if not ready.

### Component Checks

**Database:**

- Tests MongoDB connection with ping command
- Returns connection status

**LLM API:**

- Checks if Groq API client can be initialized
- Verifies session is ready
- Returns model configuration

**Job Queue:**

- Checks if background job queue is running
- Returns worker count and queue size

### Usage

**Manual Health Check:**

```bash
curl http://localhost:8000/health
```

**Kubernetes Liveness Probe:**

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Kubernetes Readiness Probe:**

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Benefits

- **Service monitoring**: Monitor service health in production
- **Automatic recovery**: Enable automatic restarts with Kubernetes
- **Load balancer integration**: Remove unhealthy instances from load balancers
- **Deployment safety**: Ensure new deployments are healthy before routing traffic

## Integration Summary

### Application Startup

1. Structured logging is initialized with JSON formatter
2. Metrics collector is created
3. Background job queue is started
4. Database connection is established

### Request Processing

1. Request ID is generated and set in context
2. Request start is logged with structured logging
3. Request is processed
4. Response time is tracked in metrics
5. Request completion is logged with structured logging
6. Request ID is included in response headers

### Agent Execution

1. Agent execution starts
2. Execution is logged with structured logging
3. Execution time is tracked in metrics
4. Execution result is logged
5. Metrics are stored in database

### Error Handling

1. Errors are caught by middleware
2. Full context and stack trace are logged
3. Error is tracked in metrics
4. User-friendly error response is returned

## Monitoring Best Practices

### Log Analysis

**Search by Request ID:**

```bash
grep '"request_id":"uuid-here"' server.log
```

**Search by Error Type:**

```bash
grep '"event_type":"error"' server.log | grep '"error_type":"ValidationError"'
```

**Search by Agent:**

```bash
grep '"agent_name":"SpecParser"' server.log
```

### Metrics Analysis

**Check API Performance:**

```bash
curl http://localhost:8000/metrics | jq '.metrics.api'
```

**Check Agent Performance:**

```bash
curl http://localhost:8000/metrics | jq '.metrics.agents'
```

**Identify Slow Operations:**

```bash
curl http://localhost:8000/metrics | jq '.metrics.api | to_entries | map(select(.value.p95 > 1.0))'
```

### Health Monitoring

**Continuous Health Check:**

```bash
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

**Alert on Unhealthy Status:**

```bash
status=$(curl -s http://localhost:8000/health | jq -r '.status')
if [ "$status" != "healthy" ]; then
  echo "Service is $status!"
fi
```

## Production Deployment

### Log Aggregation

Recommended tools:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch Logs** (AWS)

### Metrics Monitoring

Recommended tools:

- **Prometheus** + **Grafana**
- **Datadog**
- **New Relic**
- **CloudWatch** (AWS)

### Alerting

Set up alerts for:

- High error rates (>5% of requests)
- Slow response times (p95 > 1s)
- Unhealthy status
- High LLM API latency
- Database connection failures

### Log Retention

Recommended retention periods:

- **Application logs**: 30 days
- **Error logs**: 90 days
- **Audit logs**: 1 year
- **Metrics**: 90 days (aggregated: 1 year)

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 19.5**: Error logging completeness with structured JSON format
- **Requirement 16.5**: Agent performance metrics tracking
- **All Requirements**: Health check endpoints for all components

## Testing

All monitoring and logging features have been tested and verified:

- Structured logging: ✓ Passed
- Performance metrics: ✓ Passed
- Metrics statistics: ✓ Passed
- Metrics timer: ✓ Passed

## Future Enhancements

Potential improvements for future iterations:

1. **Distributed Tracing**: OpenTelemetry integration for distributed tracing
2. **Custom Dashboards**: Pre-built Grafana dashboards for common metrics
3. **Anomaly Detection**: ML-based anomaly detection for metrics
4. **Log Sampling**: Sample high-volume logs to reduce storage costs
5. **Real-time Alerts**: Integration with PagerDuty, Slack, etc.
6. **Performance Profiling**: Integration with profiling tools (py-spy, cProfile)

## Conclusion

The monitoring and logging system provides comprehensive observability for the SVA-Chatbot:

- **Structured logging** enables easy log analysis and debugging
- **Performance metrics** enable performance monitoring and optimization
- **Health checks** enable reliable production deployments

This foundation supports production operations, troubleshooting, and continuous improvement of the system.
