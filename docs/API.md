# SVA-Chatbot API Documentation

Complete API reference for the SVA-Chatbot backend service.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.your-domain.com`

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Get Authentication Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## API Endpoints

### Health & Status

#### GET /health

Comprehensive health check for all system components.

**Authentication**: Not required

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-17T00:00:00.000000",
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
      "queue_size": 0
    }
  }
}
```

#### GET /health/live

Liveness probe for container orchestration.

**Authentication**: Not required

**Response:**

```json
{
  "status": "alive"
}
```

#### GET /health/ready

Readiness probe for container orchestration.

**Authentication**: Not required

**Response:**

```json
{
  "status": "ready"
}
```

### Metrics & Monitoring

#### GET /metrics

Get performance metrics for all tracked operations.

**Authentication**: Not required

**Response:**

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

#### GET /cache/stats

Get cache statistics for performance monitoring.

**Authentication**: Not required

**Response:**

```json
{
  "cache_stats": {
    "pattern_cache": {
      "size": 45,
      "hits": 234,
      "misses": 67,
      "hit_rate": "77.74%"
    },
    "llm_cache": {
      "size": 123,
      "hits": 456,
      "misses": 89,
      "hit_rate": "83.67%"
    },
    "query_cache": {
      "size": 78,
      "hits": 890,
      "misses": 123,
      "hit_rate": "87.86%"
    }
  }
}
```

### Projects

#### POST /api/projects

Create a new project.

**Authentication**: Required

**Request:**

```json
{
  "name": "My Verification Project",
  "description": "AXI protocol verification"
}
```

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "My Verification Project",
  "description": "AXI protocol verification",
  "status": "draft",
  "created_at": "2026-01-17T00:00:00.000000",
  "updated_at": "2026-01-17T00:00:00.000000",
  "user_id": "user123",
  "metadata": {
    "total_specs": 0,
    "total_rtl_files": 0,
    "total_assertions": 0
  }
}
```

#### GET /api/projects

List all projects for the authenticated user.

**Authentication**: Required

**Query Parameters:**

- `limit` (optional): Maximum number of results (default: 50)
- `skip` (optional): Number of results to skip (default: 0)
- `status` (optional): Filter by status (draft, processing, completed, failed)

**Response:**

```json
{
  "projects": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "My Verification Project",
      "description": "AXI protocol verification",
      "status": "completed",
      "created_at": "2026-01-17T00:00:00.000000",
      "metadata": {
        "total_specs": 2,
        "total_rtl_files": 3,
        "total_assertions": 45
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "skip": 0
}
```

#### GET /api/projects/{id}

Get a specific project by ID.

**Authentication**: Required

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "My Verification Project",
  "description": "AXI protocol verification",
  "status": "completed",
  "created_at": "2026-01-17T00:00:00.000000",
  "updated_at": "2026-01-17T00:00:00.000000",
  "user_id": "user123",
  "metadata": {
    "total_specs": 2,
    "total_rtl_files": 3,
    "total_assertions": 45
  }
}
```

#### DELETE /api/projects/{id}

Delete a project and all associated data.

**Authentication**: Required

**Response:**

```json
{
  "message": "Project deleted successfully",
  "deleted_count": {
    "specifications": 2,
    "rtl_designs": 3,
    "assertions": 45
  }
}
```

### File Upload

#### POST /api/projects/{id}/upload-spec

Upload a specification document.

**Authentication**: Required

**Request:**

```http
POST /api/projects/{id}/upload-spec
Content-Type: multipart/form-data

file: <specification-file>
```

**Supported formats**: PDF, DOCX, MD, TXT

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439012",
  "project_id": "507f1f77bcf86cd799439011",
  "filename": "axi_spec.pdf",
  "file_type": "pdf",
  "file_size": 1048576,
  "uploaded_at": "2026-01-17T00:00:00.000000",
  "processed": false
}
```

#### POST /api/projects/{id}/upload-rtl

Upload an RTL design file.

**Authentication**: Required

**Request:**

```http
POST /api/projects/{id}/upload-rtl
Content-Type: multipart/form-data

file: <rtl-file>
```

**Supported formats**: .sv, .v

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439013",
  "project_id": "507f1f77bcf86cd799439011",
  "filename": "axi_slave.sv",
  "file_type": "sv",
  "file_size": 524288,
  "uploaded_at": "2026-01-17T00:00:00.000000",
  "processed": false
}
```

### Generation

#### POST /api/projects/{id}/generate

Start assertion generation for a project.

**Authentication**: Required

**Response:**

```json
{
  "job_id": "gen_507f1f77bcf86cd799439014",
  "status": "queued",
  "message": "Generation started"
}
```

#### GET /api/projects/{id}/status

Get generation status for a project.

**Authentication**: Required

**Response:**

```json
{
  "status": "processing",
  "current_agent": "RTLAnalyzer",
  "progress": 0.4,
  "started_at": "2026-01-17T00:00:00.000000",
  "estimated_completion": "2026-01-17T00:02:00.000000"
}
```

### Assertions

#### GET /api/assertions

Get assertions for a project.

**Authentication**: Required

**Query Parameters:**

- `project_id` (required): Project ID
- `limit` (optional): Maximum number of results (default: 100)
- `skip` (optional): Number of results to skip (default: 0)
- `type` (optional): Filter by type (immediate, concurrent, property, sequence)
- `category` (optional): Filter by category

**Response:**

```json
{
  "assertions": [
    {
      "id": "507f1f77bcf86cd799439015",
      "project_id": "507f1f77bcf86cd799439011",
      "requirement_id": "req_001",
      "assertion_code": "assert property (@(posedge clk) disable iff (!rst_n)\n  awvalid |-> ##[1:16] awready\n);",
      "assertion_type": "concurrent",
      "category": "protocol",
      "confidence_score": 0.92,
      "quality_score": 0.88,
      "explanation": "Validates that AWREADY must respond within 16 cycles of AWVALID",
      "traceability": {
        "spec_reference": "req_001",
        "requirement_text": "The slave must respond to AWVALID within 16 cycles",
        "rtl_signals": ["awvalid", "awready"],
        "rtl_module": "axi_slave",
        "line_numbers": [45, 67]
      },
      "generated_at": "2026-01-17T00:00:00.000000"
    }
  ],
  "total": 45,
  "limit": 100,
  "skip": 0
}
```

#### GET /api/assertions/{id}

Get a specific assertion by ID.

**Authentication**: Required

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439015",
  "project_id": "507f1f77bcf86cd799439011",
  "requirement_id": "req_001",
  "assertion_code": "assert property (@(posedge clk) disable iff (!rst_n)\n  awvalid |-> ##[1:16] awready\n);",
  "assertion_type": "concurrent",
  "category": "protocol",
  "confidence_score": 0.92,
  "quality_score": 0.88,
  "explanation": "Validates that AWREADY must respond within 16 cycles of AWVALID",
  "traceability": {
    "spec_reference": "req_001",
    "requirement_text": "The slave must respond to AWVALID within 16 cycles",
    "rtl_signals": ["awvalid", "awready"],
    "rtl_module": "axi_slave",
    "line_numbers": [45, 67]
  },
  "validation": {
    "syntax_valid": true,
    "vacuity_check": "passed",
    "quality_score": 0.88
  },
  "user_feedback": {
    "rating": null,
    "modified": false,
    "comments": null
  },
  "generated_at": "2026-01-17T00:00:00.000000"
}
```

#### PUT /api/assertions/{id}

Update an assertion.

**Authentication**: Required

**Request:**

```json
{
  "assertion_code": "assert property (@(posedge clk) disable iff (!rst_n)\n  awvalid |-> ##[1:8] awready\n);",
  "comments": "Reduced timeout to 8 cycles"
}
```

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439015",
  "assertion_code": "assert property (@(posedge clk) disable iff (!rst_n)\n  awvalid |-> ##[1:8] awready\n);",
  "user_feedback": {
    "modified": true,
    "comments": "Reduced timeout to 8 cycles"
  },
  "updated_at": "2026-01-17T00:01:00.000000"
}
```

#### POST /api/assertions/{id}/feedback

Submit feedback for an assertion.

**Authentication**: Required

**Request:**

```json
{
  "rating": 5,
  "comments": "Perfect assertion, works as expected"
}
```

**Response:**

```json
{
  "message": "Feedback submitted successfully",
  "assertion_id": "507f1f77bcf86cd799439015",
  "rating": 5
}
```

### Export

#### GET /api/projects/{id}/export

Export all assertions for a project as an SVA file.

**Authentication**: Required

**Query Parameters:**

- `format` (optional): Export format (sva, json) (default: sva)
- `include_comments` (optional): Include traceability comments (default: true)

**Response:**

```systemverilog
// SVA-Chatbot Generated Assertions
// Project: My Verification Project
// Generated: 2026-01-17T00:00:00.000000

// Requirement: req_001
// The slave must respond to AWVALID within 16 cycles
// Confidence: 0.92, Quality: 0.88
assert property (@(posedge clk) disable iff (!rst_n)
  awvalid |-> ##[1:16] awready
);

// ... more assertions ...
```

#### GET /api/projects/{id}/export/traceability

Export traceability matrix.

**Authentication**: Required

**Query Parameters:**

- `format` (optional): Export format (json, csv, markdown) (default: json)

**Response:**

```json
{
  "project_id": "507f1f77bcf86cd799439011",
  "project_name": "My Verification Project",
  "generated_at": "2026-01-17T00:00:00.000000",
  "requirements": [
    {
      "id": "req_001",
      "text": "The slave must respond to AWVALID within 16 cycles",
      "assertions": ["507f1f77bcf86cd799439015"],
      "coverage": 1.0
    }
  ],
  "coverage_summary": {
    "total_requirements": 25,
    "covered_requirements": 23,
    "coverage_percentage": 92.0
  }
}
```

### WebSocket

#### WS /ws/generation

WebSocket endpoint for real-time generation updates.

**Authentication**: Required (via query parameter `token`)

**Connection:**

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/ws/generation?token=<jwt-token>&project_id=<project-id>"
);
```

**Messages:**

**Status Update:**

```json
{
  "type": "status",
  "agent": "SpecParser",
  "status": "completed",
  "message": "Parsed 25 requirements",
  "timestamp": "2026-01-17T00:00:00.000000"
}
```

**Assertion Generated:**

```json
{
  "type": "assertion",
  "assertion": {
    "id": "507f1f77bcf86cd799439015",
    "code": "assert property ...",
    "confidence_score": 0.92
  },
  "timestamp": "2026-01-17T00:00:00.000000"
}
```

**Error:**

```json
{
  "type": "error",
  "error": "Failed to parse RTL file",
  "details": "Syntax error at line 45",
  "timestamp": "2026-01-17T00:00:00.000000"
}
```

**Clarification:**

```json
{
  "type": "clarification",
  "question": "Which clock signal should be used for this assertion?",
  "options": ["clk", "axi_clk", "sys_clk"],
  "timestamp": "2026-01-17T00:00:00.000000"
}
```

### Background Jobs

#### GET /jobs/{job_id}

Get status of a background job.

**Authentication**: Not required

**Response:**

```json
{
  "job_id": "gen_507f1f77bcf86cd799439014",
  "description": "Processing large specification file",
  "status": "running",
  "progress": 0.65,
  "created_at": "2026-01-17T00:00:00.000000",
  "started_at": "2026-01-17T00:00:01.000000",
  "completed_at": null,
  "error": null
}
```

## Error Responses

All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2026-01-17T00:00:00.000000",
  "request_id": "uuid"
}
```

### Common Error Codes

| Status Code | Error Code            | Description                       |
| ----------- | --------------------- | --------------------------------- |
| 400         | `invalid_request`     | Invalid request parameters        |
| 401         | `unauthorized`        | Missing or invalid authentication |
| 403         | `forbidden`           | Insufficient permissions          |
| 404         | `not_found`           | Resource not found                |
| 413         | `file_too_large`      | Uploaded file exceeds size limit  |
| 422         | `validation_error`    | Request validation failed         |
| 429         | `rate_limit_exceeded` | Too many requests                 |
| 500         | `internal_error`      | Internal server error             |
| 503         | `service_unavailable` | Service temporarily unavailable   |

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642377600
```

## Pagination

List endpoints support pagination:

**Query Parameters:**

- `limit`: Maximum number of results (default: 50, max: 100)
- `skip`: Number of results to skip (default: 0)

**Response includes:**

```json
{
  "items": [...],
  "total": 250,
  "limit": 50,
  "skip": 0,
  "has_more": true
}
```

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Code Examples

### Python

```python
import requests

# Authentication
response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={'username': 'user@example.com', 'password': 'password'}
)
token = response.json()['access_token']

# Create project
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8000/api/projects',
    headers=headers,
    json={'name': 'My Project', 'description': 'Test project'}
)
project_id = response.json()['id']

# Upload specification
files = {'file': open('spec.pdf', 'rb')}
response = requests.post(
    f'http://localhost:8000/api/projects/{project_id}/upload-spec',
    headers=headers,
    files=files
)
```

### JavaScript

```javascript
// Authentication
const response = await fetch("http://localhost:8000/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "user@example.com",
    password: "password",
  }),
});
const { access_token } = await response.json();

// Create project
const projectResponse = await fetch("http://localhost:8000/api/projects", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${access_token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    name: "My Project",
    description: "Test project",
  }),
});
const { id: projectId } = await projectResponse.json();

// WebSocket connection
const ws = new WebSocket(
  `ws://localhost:8000/ws/generation?token=${access_token}&project_id=${projectId}`
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Received:", message);
};
```

### cURL

```bash
# Authentication
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Create project
PROJECT_ID=$(curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project","description":"Test project"}' \
  | jq -r '.id')

# Upload specification
curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/upload-spec \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@spec.pdf"

# Get assertions
curl http://localhost:8000/api/assertions?project_id=$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN"
```

## Support

For API issues or questions:

- GitHub Issues: https://github.com/your-org/sva-chatbot/issues
- Email: api-support@your-domain.com
- Documentation: https://docs.your-domain.com
