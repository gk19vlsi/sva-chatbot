# SVA-Chatbot - Complete Project Documentation

**Version:** 2.0.0  
**Last Updated:** February 3, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Features](#features)
5. [Setup & Installation](#setup--installation)
6. [Configuration](#configuration)
7. [API Documentation](#api-documentation)
8. [Multi-Agent Pipeline](#multi-agent-pipeline)
9. [LLM Provider Integration](#llm-provider-integration)
10. [Database Schema](#database-schema)
11. [Frontend Components](#frontend-components)
12. [Security](#security)
13. [Testing](#testing)
14. [Deployment](#deployment)
15. [Troubleshooting](#troubleshooting)
16. [Contributing](#contributing)
17. [License](#license)

---

## Project Overview

### What is SVA-Chatbot?

SVA-Chatbot is an intelligent AI-powered system that automatically generates SystemVerilog Assertions (SVA) from natural language specifications and RTL designs. It uses a multi-agent pipeline architecture to analyze requirements, understand RTL code, and generate high-quality, syntactically correct assertions with full traceability.

### Key Capabilities

- **Automated Assertion Generation**: Convert natural language specifications into SVA code
- **Multi-Format Support**: Process PDF, DOCX, Markdown, and TXT specifications
- **RTL Analysis**: Parse and understand SystemVerilog/Verilog designs
- **Intelligent Alignment**: Map requirements to RTL implementations
- **Quality Assurance**: Validate and score generated assertions
- **Full Traceability**: Track requirements → assertions → RTL signals
- **Real-time Monitoring**: WebSocket-based progress updates
- **Interactive Refinement**: Edit and improve assertions with AI assistance
- **Multiple Export Formats**: SVA, JSON, Markdown

### Use Cases

1. **Verification Engineers**: Accelerate assertion development for testbenches
2. **Design Teams**: Ensure design intent is captured in assertions
3. **Quality Assurance**: Maintain traceability between specs and verification
4. **Education**: Learn SVA through AI-generated examples

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  - File Upload UI                                       │ │
│  │  - Real-time Progress Monitoring (WebSocket)            │ │
│  │  - Assertion Viewer & Editor                            │ │
│  │  - Traceability Matrix                                  │ │
│  │  - Export & Feedback System                             │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API / WebSocket
┌──────────────────────┴──────────────────────────────────────┐
│                Backend (FastAPI + Python)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Multi-Agent Pipeline                       │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  1. Specification Parser Agent                    │  │ │
│  │  │     - Extract requirements from documents         │  │ │
│  │  │     - Parse temporal constraints                  │  │ │
│  │  │  2. RTL Analyzer Agent                            │  │ │
│  │  │     - Parse SystemVerilog/Verilog                 │  │ │
│  │  │     - Extract signals and modules                 │  │ │
│  │  │  3. Alignment Agent                               │  │ │
│  │  │     - Map requirements to RTL                     │  │ │
│  │  │     - Identify signal relationships               │  │ │
│  │  │  4. SVA Generator Agent                           │  │ │
│  │  │     - Generate assertion code                     │  │ │
│  │  │     - Apply best practices                        │  │ │
│  │  │  5. Validation Agent                              │  │ │
│  │  │     - Validate syntax                             │  │ │
│  │  │     - Score quality and confidence                │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              LLM Provider Layer                         │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │  LLMClientFactory (Provider Abstraction)          │  │ │
│  │  │    ├─ GroqClient (Groq API)                       │  │ │
│  │  │    └─ OpenAIClient (OpenAI API)                   │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   MongoDB Database                           │
│  - Projects, Specifications, RTL Designs                     │
│  - Assertions, Feedback, Traceability                        │
│  - Users, Authentication                                     │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Modularity**: Each agent has a single, well-defined responsibility
2. **Extensibility**: Easy to add new agents or LLM providers
3. **Scalability**: Async operations and background job processing
4. **Reliability**: Comprehensive error handling and fallback mechanisms
5. **Observability**: Structured logging and metrics tracking

---

## Technology Stack

### Backend

| Technology      | Version | Purpose                 |
| --------------- | ------- | ----------------------- |
| **Python**      | 3.11+   | Core language           |
| **FastAPI**     | 0.115.0 | Web framework           |
| **Motor**       | 3.6.0   | Async MongoDB driver    |
| **Pydantic**    | 2.10.5  | Data validation         |
| **PyMuPDF**     | 1.24.14 | PDF text extraction     |
| **python-docx** | 1.1.2   | DOCX processing         |
| **tree-sitter** | 0.21.3  | SystemVerilog parsing   |
| **aiohttp**     | 3.11.11 | Async HTTP client       |
| **Groq SDK**    | Latest  | Groq API integration    |
| **OpenAI SDK**  | 1.0.0+  | OpenAI API integration  |
| **WebSockets**  | 14.1    | Real-time communication |
| **pytest**      | 8.3.4   | Testing framework       |
| **Hypothesis**  | 6.122.4 | Property-based testing  |

### Frontend

| Technology        | Version | Purpose      |
| ----------------- | ------- | ------------ |
| **React**         | 18.x    | UI framework |
| **TypeScript**    | 5.x     | Type safety  |
| **Vite**          | 5.4.21  | Build tool   |
| **Tailwind CSS**  | 3.x     | Styling      |
| **Monaco Editor** | Latest  | Code editor  |
| **React Router**  | 6.x     | Routing      |
| **Axios**         | Latest  | HTTP client  |
| **Vitest**        | Latest  | Testing      |

### Infrastructure

| Technology         | Purpose                       |
| ------------------ | ----------------------------- | -------- |
| **MongoDB**        | 7.0+                          | Database |
| **Docker**         | Containerization              |
| **Docker Compose** | Multi-container orchestration |
| **Nginx**          | Reverse proxy (production)    |

### Development Tools

- **Git** - Version control
- **ESLint** - JavaScript linting
- **Prettier** - Code formatting
- **Black** - Python formatting
- **mypy** - Python type checking

---

## Features

### ✅ Completed Features

#### 1. File Upload & Processing

- **Specification Formats**: PDF, DOCX, Markdown, TXT
- **RTL Formats**: SystemVerilog (.sv), Verilog (.v)
- **File Size Limit**: 50 MB per file
- **Text Extraction**: Automatic text extraction with OCR detection
- **Validation**: File type and content validation

#### 2. Multi-Agent Pipeline

- **5 Specialized Agents**: Each with specific responsibilities
- **Sequential Processing**: Orchestrated workflow
- **Error Recovery**: Graceful handling of agent failures
- **Progress Tracking**: Real-time status updates

#### 3. LLM Provider Support

- **Groq API**: Fast inference with Llama models
- **OpenAI API**: GPT-4 and GPT-4-mini support
- **Provider Switching**: Configuration-based selection
- **Fallback Models**: Automatic fallback on rate limits
- **Token Tracking**: Per-project usage monitoring

#### 4. Assertion Generation

- **Automatic Generation**: From natural language specs
- **Syntax Validation**: Real-time SVA syntax checking
- **Quality Scoring**: Confidence and quality metrics
- **Type Classification**: Immediate, concurrent, property, sequence
- **Traceability**: Full requirement-to-assertion-to-RTL mapping

#### 5. User Interface

- **Dashboard**: Project overview and management
- **File Upload**: Drag-and-drop interface
- **Assertion Viewer**: Side-by-side spec/RTL/assertion view
- **Code Editor**: Monaco-based with syntax highlighting
- **Traceability Matrix**: Visual requirement coverage
- **Export Options**: SVA, JSON, Markdown formats

#### 6. Real-time Features

- **WebSocket Updates**: Live progress monitoring
- **Agent Status**: Current agent and progress percentage
- **Error Notifications**: Immediate error feedback
- **Completion Alerts**: Success notifications

#### 7. Quality & Refinement

- **Edit Mode**: Modify generated assertions
- **Syntax Validation**: Real-time error detection
- **Feedback System**: Rate and comment on assertions
- **Regeneration**: Request improved versions
- **Version History**: Track modifications

#### 8. Security & Authentication

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt encryption
- **Input Sanitization**: XSS and injection prevention
- **Rate Limiting**: 100 requests/minute default
- **HTTPS Support**: TLS/SSL in production

#### 9. Performance Optimization

- **Response Caching**: LLM response caching (5-minute TTL)
- **Database Indexing**: Optimized queries
- **Background Jobs**: Async task processing
- **Connection Pooling**: Efficient resource usage
- **Query Optimization**: Reduced database load

#### 10. Monitoring & Logging

- **Structured Logging**: JSON-formatted logs
- **Metrics Tracking**: Request duration, success rates
- **Error Tracking**: Detailed error logs with stack traces
- **Health Checks**: System status endpoints
- **Performance Metrics**: Token usage, API latency

---

## Setup & Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **MongoDB**: 7.0 or higher
- **Git**: Latest version
- **API Keys**: Groq API key and/or OpenAI API key

### Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/sva-chatbot.git
cd sva-chatbot

# 2. Configure environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with your API keys:
# - GROQ_API_KEY=your_groq_key
# - OPENAI_API_KEY=your_openai_key (optional)
# - LLM_PROVIDER=groq (or openai)

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start MongoDB (if not using Docker)
mongod --dbpath /path/to/data

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the startup script
bash start_dev.sh
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with backend URL

# Run development server
npm run dev

# Access at http://localhost:3000
```

### Database Setup

MongoDB will automatically create collections and indexes on first run. No manual setup required.

### Verification

```bash
# Check backend health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs

# Check frontend
open http://localhost:3000
```

---

## Configuration

### Backend Configuration (.env)

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=sva_chatbot

# LLM Provider Selection
LLM_PROVIDER=groq  # Options: groq, openai

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_PRIMARY_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant

# OpenAI API Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_PRIMARY_MODEL=gpt-4o
OPENAI_FALLBACK_MODEL=gpt-4o-mini

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Security
ENCRYPTION_KEY=your-encryption-key-32-bytes
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# File Upload
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=./uploads

# Caching
CACHE_TTL_SECONDS=300
ENABLE_CACHE=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=server.log

# Background Jobs
JOB_QUEUE_WORKERS=5
```

### Frontend Configuration (.env)

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000

# Environment
VITE_ENV=development
```

### LLM Provider Configuration

#### Using Groq (Default)

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

**Advantages:**

- Fast inference (< 1 second)
- Cost-effective
- Good for development

#### Using OpenAI

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
```

**Advantages:**

- Higher quality outputs
- Better reasoning
- More reliable

#### Switching Providers

Simply change `LLM_PROVIDER` in `.env` and restart the backend. No code changes required!

---

## API Documentation

### Authentication Endpoints

#### POST /api/auth/register

Register a new user account.

**Request:**

```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /api/auth/login

Login with existing credentials.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Project Endpoints

#### POST /api/projects

Create a new project.

**Headers:**

```
Authorization: Bearer <token>
```

**Request:**

```json
{
  "name": "AXI Protocol Verification",
  "description": "Generate assertions for AXI4 interface"
}
```

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "AXI Protocol Verification",
  "description": "Generate assertions for AXI4 interface",
  "status": "created",
  "created_at": "2026-02-03T10:00:00Z"
}
```

#### GET /api/projects

List all projects for the authenticated user.

**Response:**

```json
{
  "projects": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "AXI Protocol Verification",
      "status": "completed",
      "created_at": "2026-02-03T10:00:00Z",
      "metadata": {
        "total_assertions": 15
      }
    }
  ]
}
```

#### POST /api/projects/{project_id}/upload-specification

Upload specification file.

**Headers:**

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**

- `file`: Specification file (PDF, DOCX, MD, TXT)

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439012",
  "filename": "axi_spec.pdf",
  "file_type": "pdf",
  "file_size": 245760,
  "uploaded_at": "2026-02-03T10:05:00Z"
}
```

#### POST /api/projects/{project_id}/upload-rtl

Upload RTL design file.

**Headers:**

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**

- `file`: RTL file (.sv, .v)

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439013",
  "filename": "axi_slave.sv",
  "file_type": "sv",
  "file_size": 12800,
  "uploaded_at": "2026-02-03T10:10:00Z"
}
```

#### POST /api/projects/{project_id}/generate-assertions

Start assertion generation pipeline.

**Response:**

```json
{
  "success": true,
  "project_id": "507f1f77bcf86cd799439011",
  "assertions_generated": 15,
  "message": "Successfully generated 15 assertions"
}
```

### Assertion Endpoints

#### GET /api/assertions/project/{project_id}

Get all assertions for a project.

**Response:**

```json
{
  "project_id": "507f1f77bcf86cd799439011",
  "total": 15,
  "assertions": [
    {
      "id": "507f1f77bcf86cd799439014",
      "code": "assert property (@(posedge clk) awvalid |-> ##[1:16] awready);",
      "type": "concurrent",
      "category": "functional",
      "confidence_score": 0.95,
      "quality_score": 0.92,
      "explanation": "Validates AWREADY response within 16 cycles",
      "traceability": {
        "requirement_text": "Slave must respond within 16 cycles",
        "rtl_signals": ["awvalid", "awready"],
        "rtl_module": "axi_slave"
      }
    }
  ]
}
```

#### PUT /api/assertions/{assertion_id}

Update an assertion.

**Request:**

```json
{
  "code": "assert property (@(posedge clk) awvalid |-> ##[1:8] awready);"
}
```

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439014",
  "code": "assert property (@(posedge clk) awvalid |-> ##[1:8] awready);",
  "modified": true,
  "modified_at": "2026-02-03T10:30:00Z"
}
```

### Export Endpoints

#### GET /api/projects/{project_id}/export

Export assertions in various formats.

**Query Parameters:**

- `format`: sva, json, markdown

**Response:** File download

### WebSocket Endpoints

#### WS /ws/{project_id}

Real-time progress updates during assertion generation.

**Messages:**

```json
{
  "type": "progress",
  "agent": "spec_parser",
  "progress": 20,
  "message": "Parsing specification..."
}
```

---

## Multi-Agent Pipeline

### Pipeline Overview

The assertion generation process uses 5 specialized agents that work sequentially:

```
Specification → Parser → RTL Analyzer → Alignment → Generator → Validator → Assertions
```

### Agent 1: Specification Parser

**Purpose:** Extract and structure requirements from specification documents

**Input:**

- Raw specification text (from PDF, DOCX, MD, TXT)

**Processing:**

1. Identify requirement statements
2. Extract temporal constraints (within, after, before)
3. Parse signal names and conditions
4. Structure requirements with IDs

**Output:**

```json
{
  "requirements": [
    {
      "id": "REQ-001",
      "text": "The slave MUST respond to AWVALID within 16 clock cycles",
      "temporal_constraint": "within 16 cycles",
      "signals": ["AWVALID", "AWREADY"],
      "type": "timing"
    }
  ]
}
```

### Agent 2: RTL Analyzer

**Purpose:** Parse and understand RTL design structure

**Input:**

- SystemVerilog/Verilog code

**Processing:**

1. Parse module definitions
2. Extract signal declarations
3. Identify clock and reset signals
4. Build signal dependency graph
5. Extract state machines

**Output:**

```json
{
  "modules": [
    {
      "name": "axi_slave",
      "signals": {
        "inputs": ["clk", "rst_n", "awvalid"],
        "outputs": ["awready"],
        "internal": ["state"]
      },
      "clock": "clk",
      "reset": "rst_n"
    }
  ]
}
```

### Agent 3: Alignment Agent

**Purpose:** Map requirements to RTL implementations

**Input:**

- Parsed requirements
- RTL structure

**Processing:**

1. Match requirement signals to RTL signals
2. Identify relevant modules
3. Determine signal relationships
4. Map temporal constraints to RTL timing

**Output:**

```json
{
  "alignments": [
    {
      "requirement_id": "REQ-001",
      "rtl_module": "axi_slave",
      "signal_mapping": {
        "AWVALID": "awvalid",
        "AWREADY": "awready"
      },
      "clock_signal": "clk",
      "reset_signal": "rst_n"
    }
  ]
}
```

### Agent 4: SVA Generator

**Purpose:** Generate SystemVerilog Assertion code

**Input:**

- Aligned requirements and RTL

**Processing:**

1. Select appropriate assertion type
2. Generate temporal operators
3. Apply SVA best practices
4. Add comments and documentation
5. Format code properly

**Output:**

```systemverilog
// Requirement REQ-001: Slave must respond within 16 cycles
// Module: axi_slave
// Signals: awvalid, awready
assert property (@(posedge clk) disable iff (!rst_n)
  awvalid |-> ##[1:16] awready
) else $error("AWVALID timeout");
```

### Agent 5: Validation Agent

**Purpose:** Validate and score generated assertions

**Input:**

- Generated assertion code

**Processing:**

1. Syntax validation
2. Semantic analysis
3. Calculate confidence score
4. Calculate quality score
5. Identify potential issues

**Output:**

```json
{
  "assertion_id": "AST-001",
  "syntax_valid": true,
  "confidence_score": 0.95,
  "quality_score": 0.92,
  "issues": [],
  "recommendations": []
}
```

### Pipeline Orchestration

The `Orchestrator` class manages the pipeline:

```python
class Orchestrator:
    def __init__(self, db):
        self.llm_client = LLMClientFactory.create_client()
        self.agents = {
            "spec_parser": SpecificationParserAgent(self.llm_client, db),
            "rtl_analyzer": RTLAnalyzerAgent(self.llm_client, db),
            "alignment": AlignmentAgent(self.llm_client, db),
            "sva_generator": SVAGeneratorAgent(self.llm_client, db),
            "validation": ValidationAgent(self.llm_client, db)
        }

    async def run_pipeline(self, project_id, spec_text, rtl_code):
        # Execute agents sequentially
        # Handle errors and progress updates
        # Return final assertions
```

---

## LLM Provider Integration

### Architecture

The system uses a factory pattern to support multiple LLM providers:

```
LLMClientFactory
    ├── GroqClient (Groq API)
    └── OpenAIClient (OpenAI API)
```

### LLMClient Protocol

All clients implement a common interface:

```python
class LLMClient(Protocol):
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        project_id: Optional[str] = None,
        use_fallback: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Make a chat completion request"""
        ...

    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        project_id: Optional[str] = None,
        use_cache: bool = True,
        use_aggressive_fallback: bool = False
    ) -> Dict[str, Any]:
        """Make a chat completion request with automatic fallback"""
        ...

    def get_token_usage(self, project_id: str) -> Dict[str, int]:
        """Get token usage statistics for a project"""
        ...

    async def close(self) -> None:
        """Close the client session"""
        ...
```

### Groq Client

**Features:**

- Fast inference with Llama models
- Automatic fallback to smaller models
- Response caching
- Token usage tracking
- Metrics integration

**Models:**

- Primary: `llama-3.3-70b-versatile`
- Fallback: `llama-3.1-8b-instant`

**Configuration:**

```python
GROQ_API_KEY=gsk_...
GROQ_PRIMARY_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
```

### OpenAI Client

**Features:**

- High-quality outputs with GPT-4
- Automatic fallback to GPT-4-mini
- Response caching
- Token usage tracking
- Metrics integration

**Models:**

- Primary: `gpt-4o`
- Fallback: `gpt-4o-mini`

**Configuration:**

```python
OPENAI_API_KEY=sk-proj-...
OPENAI_PRIMARY_MODEL=gpt-4o
OPENAI_FALLBACK_MODEL=gpt-4o-mini
```

### Factory Pattern

The factory creates the appropriate client based on configuration:

```python
class LLMClientFactory:
    @staticmethod
    def create_client() -> Union[GroqClient, OpenAIClient]:
        provider = settings.llm_provider.lower()

        if provider == "groq":
            return GroqClient(api_key=settings.groq_api_key)
        elif provider == "openai":
            return OpenAIClient(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Invalid LLM provider: {provider}")
```

### Switching Providers

To switch between providers:

1. Update `.env` file:

```bash
LLM_PROVIDER=openai  # or groq
```

2. Restart backend:

```bash
# Docker
docker-compose restart backend

# Manual
# Stop the server (Ctrl+C)
# Start again
uvicorn app.main:app --reload
```

No code changes required!

### Fallback Mechanism

Both clients support automatic fallback:

1. **Primary Model Fails** → Try fallback model
2. **Rate Limit Hit** → Use fallback model (if aggressive_fallback enabled)
3. **Both Fail** → Return error with details

### Caching

Responses are cached for 5 minutes (configurable):

- **Cache Key**: Hash of (messages, model, temperature, max_tokens, top_p)
- **Cache Storage**: In-memory dictionary
- **TTL**: 300 seconds (default)
- **Benefits**: Reduced API calls, faster responses, cost savings

### Token Tracking

Track token usage per project:

```python
# Get usage for a project
usage = client.get_token_usage(project_id)
# Returns:
{
    "prompt_tokens": 1500,
    "completion_tokens": 800,
    "total_tokens": 2300,
    "requests": 5
}
```

### Error Handling

All errors are wrapped in `LLMAPIError`:

```python
class LLMAPIError(Exception):
    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.original_error = original_error
```

---

## Database Schema

### Collections

#### users

```javascript
{
  _id: ObjectId,
  email: String (unique, indexed),
  name: String,
  hashed_password: String,
  created_at: DateTime
}
```

#### projects

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed),
  name: String,
  description: String,
  status: String, // created, processing, completed, error
  created_at: DateTime (indexed),
  updated_at: DateTime,
  metadata: {
    total_assertions: Number,
    total_requirements: Number,
    coverage_percentage: Number
  }
}
```

#### specifications

```javascript
{
  _id: ObjectId,
  project_id: ObjectId (indexed),
  filename: String,
  file_type: String, // pdf, docx, md, txt
  file_path: String,
  file_size: Number,
  raw_text: String,
  uploaded_at: DateTime,
  processed: Boolean
}
```

#### rtl_designs

```javascript
{
  _id: ObjectId,
  project_id: ObjectId (indexed),
  filename: String,
  file_type: String, // sv, v
  file_path: String,
  file_size: Number,
  raw_code: String,
  uploaded_at: DateTime,
  parsed_modules: Array,
  parsed_signals: Array
}
```

#### assertions

```javascript
{
  _id: ObjectId,
  project_id: ObjectId (indexed),
  code: String, // SVA code
  type: String, // immediate, concurrent, property, sequence
  category: String, // functional, timing, safety
  confidence_score: Number, // 0.0 - 1.0
  quality_score: Number, // 0.0 - 1.0
  explanation: String,
  traceability: {
    requirement_text: String,
    requirement_id: String,
    rtl_signals: Array,
    rtl_module: String,
    rtl_line_numbers: Array
  },
  generated_at: DateTime,
  modified: Boolean,
  modified_at: DateTime,
  original_code: String
}
```

#### feedback

```javascript
{
  _id: ObjectId,
  assertion_id: ObjectId (indexed),
  user_id: ObjectId,
  rating: Number, // 1-5
  comment: String,
  created_at: DateTime
}
```

### Indexes

```javascript
// users
db.users.createIndex({ email: 1 }, { unique: true });

// projects
db.projects.createIndex({ user_id: 1, created_at: -1 });
db.projects.createIndex({ user_id: 1, status: 1 });

// specifications
db.specifications.createIndex({ project_id: 1 });

// rtl_designs
db.rtl_designs.createIndex({ project_id: 1 });

// assertions
db.assertions.createIndex({ project_id: 1 });
db.assertions.createIndex({ project_id: 1, confidence_score: -1 });

// feedback
db.feedback.createIndex({ assertion_id: 1 });
db.feedback.createIndex({ user_id: 1, created_at: -1 });
```

---

## Frontend Components

### Component Hierarchy

```
App
├── AuthContext (Authentication state)
├── Router
│   ├── Login
│   ├── Home (Dashboard)
│   ├── Projects
│   ├── Upload
│   │   ├── FileUpload (Spec & RTL)
│   │   └── Progress Monitor
│   └── Assertions
│       ├── AssertionList
│       ├── AssertionViewer
│       │   ├── Monaco Editor
│       │   └── Metadata Display
│       ├── SideBySideViewer
│       │   ├── Specification Panel
│       │   ├── RTL Panel
│       │   └── Assertion Panel
│       └── TraceabilityMatrix
└── Navigation
```

### Key Components

#### 1. FileUpload Component

**Purpose:** Handle file uploads for specifications and RTL

**Features:**

- Drag-and-drop interface
- File type validation
- Size limit checking
- Progress indication
- Error handling

**Usage:**

```tsx
<FileUpload
  projectId={projectId}
  fileType="specification"
  onUploadSuccess={handleSuccess}
  onUploadError={handleError}
/>
```

#### 2. AssertionViewer Component

**Purpose:** Display and edit individual assertions

**Features:**

- Syntax-highlighted code editor
- Confidence and quality scores
- Traceability information
- Edit mode with validation
- Copy to clipboard
- Feedback submission

**Props:**

```typescript
interface AssertionViewerProps {
  assertion: Assertion;
  readOnly?: boolean;
  onCodeChange?: (code: string) => void;
  onSave?: (code: string) => Promise<void>;
  enableEdit?: boolean;
  enableFeedback?: boolean;
}
```

#### 3. SideBySideViewer Component

**Purpose:** Show spec, RTL, and assertion side-by-side

**Features:**

- Three-panel layout
- Signal highlighting
- Click-to-navigate
- Synchronized scrolling
- Traceability visualization

**Usage:**

```tsx
<SideBySideViewer
  assertion={selectedAssertion}
  specificationText={specText}
  rtlCode={rtlCode}
/>
```

#### 4. TraceabilityMatrix Component

**Purpose:** Visualize requirement coverage

**Features:**

- Requirement-to-assertion mapping
- Coverage statistics
- Interactive navigation
- Export functionality

**Data Structure:**

```typescript
interface TraceabilityData {
  requirements: Requirement[];
  assertions: Assertion[];
  coverage: {
    total_requirements: number;
    covered_requirements: number;
    coverage_percentage: number;
  };
}
```

#### 5. ChatInterface Component

**Purpose:** Real-time progress updates via WebSocket

**Features:**

- Live agent status
- Progress percentage
- Error notifications
- Message history

**WebSocket Messages:**

```typescript
type WebSocketMessage =
  | { type: "progress"; agent: string; progress: number; message: string }
  | { type: "error"; message: string }
  | { type: "complete"; assertions_count: number }
  | { type: "assertion"; assertion: Assertion };
```

### State Management

#### AuthContext

Manages authentication state globally:

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, name: string, password: string) => Promise<void>;
}
```

#### Local State

Components use React hooks for local state:

```typescript
const [assertions, setAssertions] = useState<Assertion[]>([]);
const [selectedAssertion, setSelectedAssertion] = useState<Assertion | null>(
  null,
);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

### Routing

```typescript
<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
  <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
  <Route path="/projects/:projectId/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
  <Route path="/projects/:projectId/assertions" element={<ProtectedRoute><Assertions /></ProtectedRoute>} />
</Routes>
```

### Styling

Uses Tailwind CSS utility classes:

```tsx
<div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
  <h2 className="text-lg font-semibold text-gray-900 mb-2">
    Assertion {index + 1}
  </h2>
  <div className="flex items-center space-x-2">
    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
      {assertion.type}
    </span>
  </div>
</div>
```

---

## Security

### Authentication & Authorization

#### JWT-Based Authentication

- **Token Generation**: HS256 algorithm
- **Token Expiration**: 60 minutes (configurable)
- **Token Storage**: LocalStorage (frontend)
- **Token Transmission**: Authorization header

#### Password Security

- **Hashing**: bcrypt with salt
- **Minimum Length**: 8 characters
- **Maximum Length**: 72 characters (bcrypt limit)
- **Storage**: Hashed passwords only

#### Authorization

- **Project Ownership**: Users can only access their own projects
- **Resource Validation**: All endpoints verify ownership
- **Token Validation**: Every protected endpoint checks JWT

### Input Sanitization

#### Middleware

```python
class SanitizationMiddleware:
    async def dispatch(self, request, call_next):
        # Sanitize query parameters
        # Sanitize request body
        # Prevent XSS attacks
        # Prevent SQL injection
```

#### File Upload Validation

- **File Type**: Whitelist of allowed extensions
- **File Size**: Maximum 50 MB
- **Content Type**: Verify MIME type
- **Filename**: Sanitize special characters

### Rate Limiting

#### Configuration

```python
RATE_LIMIT_REQUESTS=100  # requests per window
RATE_LIMIT_WINDOW=60     # seconds
```

#### Implementation

- **Per-IP Limiting**: Track requests by client IP
- **Sliding Window**: Rolling time window
- **Response**: HTTP 429 (Too Many Requests)

### HTTPS/TLS

#### Production Configuration

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### API Key Security

#### Storage

- **Environment Variables**: Never commit to git
- **Encryption**: API keys encrypted at rest
- **Access Control**: Limited to backend only

#### Best Practices

```bash
# .gitignore
.env
.env.local
*.key
*.pem
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Security Headers

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### Vulnerability Prevention

#### SQL Injection

- **MongoDB**: Parameterized queries only
- **No Raw Queries**: Use Motor's query builders

#### XSS (Cross-Site Scripting)

- **Input Sanitization**: Clean all user inputs
- **Output Encoding**: Escape HTML in responses
- **CSP Headers**: Content Security Policy

#### CSRF (Cross-Site Request Forgery)

- **SameSite Cookies**: Prevent cross-site requests
- **Token Validation**: Verify JWT on every request

#### Path Traversal

- **File Path Validation**: Sanitize file paths
- **Restricted Access**: Files only in upload directory

---

## Testing

### Backend Testing

#### Test Structure

```
backend/tests/
├── conftest.py              # Pytest fixtures
├── test_auth_properties.py  # Authentication tests
├── test_factory_unit.py     # Factory pattern tests
├── test_factory_properties.py
├── test_openai_client_unit.py
├── test_openai_client_properties.py
├── test_provider_switching_properties.py
├── test_backward_compatibility_properties.py
└── test_configuration_defaults_unit.py
```

#### Running Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_factory_unit.py -v

# Run property-based tests
pytest tests/test_*_properties.py -v
```

#### Property-Based Testing

Uses Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st

@given(
    messages=st.lists(
        st.fixed_dictionaries({
            'role': st.sampled_from(['user', 'assistant']),
            'content': st.text(min_size=1, max_size=1000)
        }),
        min_size=1,
        max_size=10
    )
)
async def test_response_format_consistency(messages):
    """Test that responses have consistent format"""
    client = OpenAIClient()
    response = await client.chat_completion(messages)

    assert "choices" in response
    assert "usage" in response
    assert response["choices"][0]["message"]["role"] == "assistant"
```

#### Unit Testing

```python
import pytest
from app.clients.factory import LLMClientFactory

def test_factory_creates_groq_client():
    """Test factory creates GroqClient when provider is groq"""
    settings.llm_provider = "groq"
    client = LLMClientFactory.create_client()
    assert isinstance(client, GroqClient)

def test_factory_creates_openai_client():
    """Test factory creates OpenAIClient when provider is openai"""
    settings.llm_provider = "openai"
    client = LLMClientFactory.create_client()
    assert isinstance(client, OpenAIClient)
```

### Frontend Testing

#### Test Structure

```
frontend/src/
├── components/
│   ├── AssertionViewer.test.tsx
│   ├── FileUpload.test.tsx
│   ├── SideBySideViewer.test.tsx
│   └── TraceabilityMatrix.test.tsx
└── setupTests.ts
```

#### Running Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- AssertionViewer.test.tsx

# Watch mode
npm test -- --watch
```

#### Component Testing

```typescript
import { render, screen } from '@testing-library/react';
import AssertionViewer from './AssertionViewer';

describe('AssertionViewer', () => {
  const mockAssertion = {
    id: 'ast-001',
    code: 'assert property (@(posedge clk) valid |-> ready);',
    type: 'concurrent',
    category: 'functional',
    confidenceScore: 0.95,
    explanation: 'Test assertion'
  };

  it('should display assertion code', () => {
    render(<AssertionViewer assertion={mockAssertion} />);
    expect(screen.getByText(/assert property/)).toBeInTheDocument();
  });

  it('should display confidence score', () => {
    render(<AssertionViewer assertion={mockAssertion} />);
    expect(screen.getByText(/95%/)).toBeInTheDocument();
  });
});
```

### Integration Testing

#### End-to-End Flow

```python
async def test_complete_assertion_generation_flow():
    """Test complete flow from upload to assertion generation"""

    # 1. Create project
    project = await create_project("Test Project")

    # 2. Upload specification
    spec = await upload_specification(project.id, "spec.txt")

    # 3. Upload RTL
    rtl = await upload_rtl(project.id, "design.sv")

    # 4. Generate assertions
    result = await generate_assertions(project.id)

    # 5. Verify assertions created
    assertions = await get_assertions(project.id)
    assert len(assertions) > 0
    assert assertions[0]["confidence_score"] > 0.7
```

### Test Coverage Goals

- **Backend**: 90% line coverage, 85% branch coverage
- **Frontend**: 80% line coverage
- **Integration**: All major user workflows
- **Property Tests**: All correctness properties

---

## Deployment

### Docker Deployment (Recommended)

#### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

#### Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# With environment variables
MONGO_ROOT_USERNAME=admin \
MONGO_ROOT_PASSWORD=secret \
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

#### Backend Deployment

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with production values

# 3. Start with gunicorn (production)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -

# Or use uvicorn (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Deployment

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Build for production
npm run build

# 3. Serve with nginx or static server
# Output is in dist/ directory
```

### Cloud Deployment

#### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
cd backend
railway up
```

#### Render

```bash
# Use render.yaml configuration
# Push to GitHub
# Connect repository in Render dashboard
```

#### Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/sva-chatbot

upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        root /var/www/sva-chatbot/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Environment Variables (Production)

```bash
# Backend
MONGODB_URL=mongodb://mongo:27017
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
JWT_SECRET_KEY=<generate-secure-key>
ENCRYPTION_KEY=<generate-32-byte-key>
ALLOWED_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO

# Frontend
VITE_API_BASE_URL=https://your-domain.com
VITE_WS_URL=wss://your-domain.com
VITE_ENV=production
```

### Health Checks

```bash
# Backend health
curl https://your-domain.com/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-03T10:00:00Z"
}
```

### Monitoring

#### Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# System logs
tail -f backend/server.log
```

#### Metrics

- Request duration
- Success/failure rates
- Token usage
- Database query performance

### Backup & Recovery

#### Database Backup

```bash
# Backup MongoDB
mongodump --uri="mongodb://localhost:27017/sva_chatbot" --out=/backup

# Restore MongoDB
mongorestore --uri="mongodb://localhost:27017/sva_chatbot" /backup/sva_chatbot
```

#### File Backup

```bash
# Backup uploads directory
tar -czf uploads-backup.tar.gz backend/uploads/

# Restore
tar -xzf uploads-backup.tar.gz -C backend/
```

---

## Troubleshooting

### Common Issues

#### 1. PDF Text Extraction Fails

**Error:**

```
Could not extract text from specification files. The uploaded PDF appears to be image-based or empty.
```

**Cause:** PDF is scanned/image-based with no extractable text

**Solution:**

- Use OCR software to convert PDF to text
- Export original document as text-based PDF
- Upload as TXT, MD, or DOCX instead

#### 2. MongoDB Connection Failed

**Error:**

```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: Connection refused
```

**Cause:** MongoDB not running or wrong connection string

**Solution:**

```bash
# Start MongoDB
mongod --dbpath /path/to/data

# Or with Docker
docker-compose up -d mongo

# Check connection string in .env
MONGODB_URL=mongodb://localhost:27017
```

#### 3. LLM API Rate Limit

**Error:**

```
[groq] Rate limit exceeded
```

**Cause:** Too many API requests

**Solution:**

- Wait for rate limit to reset
- Enable aggressive fallback in code
- Switch to OpenAI provider (higher limits)
- Upgrade API plan

#### 4. Frontend Can't Connect to Backend

**Error:**

```
Network Error: Failed to fetch
```

**Cause:** Backend not running or wrong URL

**Solution:**

```bash
# Check backend is running
curl http://localhost:8000/health

# Check frontend .env
VITE_API_BASE_URL=http://localhost:8000

# Restart frontend
npm run dev
```

#### 5. JWT Token Expired

**Error:**

```
401 Unauthorized: Token has expired
```

**Cause:** JWT token expired (default 60 minutes)

**Solution:**

- Log in again
- Increase JWT_EXPIRATION_MINUTES in backend .env
- Implement token refresh mechanism

#### 6. File Upload Fails

**Error:**

```
413 Payload Too Large
```

**Cause:** File exceeds size limit

**Solution:**

- Reduce file size
- Increase MAX_FILE_SIZE_MB in backend .env
- Split large files

#### 7. Assertion Generation Stuck

**Symptom:** Progress bar stops moving

**Cause:** Agent timeout or error

**Solution:**

```bash
# Check backend logs
docker-compose logs -f backend

# Check for errors in server.log
tail -f backend/server.log

# Restart backend
docker-compose restart backend
```

#### 8. WebSocket Connection Failed

**Error:**

```
WebSocket connection failed
```

**Cause:** WebSocket not properly configured

**Solution:**

```bash
# Check WebSocket URL in frontend .env
VITE_WS_URL=ws://localhost:8000

# For HTTPS, use wss://
VITE_WS_URL=wss://your-domain.com

# Check nginx WebSocket proxy configuration
```

### Debug Mode

#### Backend Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn app.main:app --reload --log-level debug
```

#### Frontend Debug Mode

```bash
# Enable React DevTools
# Open browser console (F12)
# Check Network tab for API calls
# Check Console tab for errors
```

### Performance Issues

#### Slow Assertion Generation

**Causes:**

- Large specification files
- Complex RTL designs
- Slow LLM API responses

**Solutions:**

- Use Groq for faster inference
- Enable response caching
- Optimize specification clarity
- Break large projects into smaller ones

#### High Memory Usage

**Causes:**

- Large file uploads
- Memory leaks
- Too many concurrent requests

**Solutions:**

```bash
# Increase Docker memory limit
docker-compose up -d --memory=4g

# Reduce concurrent workers
JOB_QUEUE_WORKERS=3

# Clear cache periodically
```

### Getting Help

#### Check Logs

```bash
# Backend logs
tail -f backend/server.log

# Docker logs
docker-compose logs -f

# Frontend console
# Open browser DevTools (F12)
```

#### Report Issues

When reporting issues, include:

1. Error message (full stack trace)
2. Steps to reproduce
3. Environment (OS, Python version, Node version)
4. Configuration (sanitized .env)
5. Logs (relevant sections)

#### Community Support

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share tips
- Email: support@your-domain.com

---

## Contributing

### Development Workflow

1. **Fork the Repository**

```bash
git clone https://github.com/your-username/sva-chatbot.git
cd sva-chatbot
```

2. **Create a Feature Branch**

```bash
git checkout -b feature/my-new-feature
```

3. **Make Changes**

- Write code
- Add tests
- Update documentation

4. **Run Tests**

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

5. **Commit Changes**

```bash
git add .
git commit -m "feat: Add new feature"
```

6. **Push and Create PR**

```bash
git push origin feature/my-new-feature
# Create Pull Request on GitHub
```

### Code Style

#### Python (Backend)

```bash
# Format with Black
black app/

# Lint with flake8
flake8 app/

# Type check with mypy
mypy app/
```

#### TypeScript (Frontend)

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Type check
npm run type-check
```

### Commit Convention

Use conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

### Pull Request Guidelines

- **Title**: Clear and descriptive
- **Description**: Explain what and why
- **Tests**: Include tests for new features
- **Documentation**: Update relevant docs
- **Breaking Changes**: Clearly marked

### Adding New Features

#### 1. New LLM Provider

```python
# 1. Create client class
class NewProviderClient:
    async def chat_completion(self, messages, **kwargs):
        # Implementation
        pass

# 2. Update factory
class LLMClientFactory:
    @staticmethod
    def create_client():
        if provider == "new_provider":
            return NewProviderClient()

# 3. Add configuration
NEW_PROVIDER_API_KEY=...
NEW_PROVIDER_MODEL=...

# 4. Add tests
def test_new_provider_client():
    # Test implementation
    pass
```

#### 2. New Agent

```python
# 1. Create agent class
class NewAgent(Agent):
    async def execute(self, data):
        # Agent logic
        return result

# 2. Add to orchestrator
self.agents["new_agent"] = NewAgent(self.llm_client, db)

# 3. Update pipeline
async def run_pipeline(self):
    # Add agent to sequence
    result = await self.agents["new_agent"].execute(data)

# 4. Add tests
async def test_new_agent():
    # Test agent
    pass
```

#### 3. New Export Format

```python
# 1. Add export function
def export_as_new_format(assertions):
    # Convert to new format
    return formatted_data

# 2. Add route
@router.get("/{project_id}/export")
async def export_assertions(format: str):
    if format == "new_format":
        return export_as_new_format(assertions)

# 3. Update frontend
const handleExport = async (format) => {
    const response = await api.get(
        `/api/projects/${projectId}/export?format=${format}`
    );
};
```

### Testing Guidelines

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test component interactions
- **Property Tests**: Test universal properties
- **E2E Tests**: Test complete workflows

### Documentation Guidelines

- Update README.md for major changes
- Add inline comments for complex logic
- Update API documentation
- Include examples in docstrings

---

## License

MIT License

Copyright (c) 2026 SVA-Chatbot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Appendix

### Project Statistics

- **Total Lines of Code**: ~15,000
- **Backend Files**: 50+
- **Frontend Files**: 30+
- **Test Files**: 35+
- **API Endpoints**: 20+
- **Database Collections**: 6
- **Supported File Formats**: 6 (PDF, DOCX, MD, TXT, SV, V)

### Technology Versions

| Component | Version | Release Date |
| --------- | ------- | ------------ |
| Python    | 3.11+   | Oct 2022     |
| FastAPI   | 0.115.0 | Sep 2024     |
| React     | 18.x    | Mar 2022     |
| MongoDB   | 7.0+    | Aug 2023     |
| Node.js   | 18+     | Apr 2022     |

### Performance Benchmarks

| Metric                    | Value       |
| ------------------------- | ----------- |
| API Response Time (p95)   | < 100ms     |
| Assertion Generation Time | 1-5 minutes |
| Cache Hit Rate            | 70-85%      |
| Database Query Time       | < 50ms      |
| WebSocket Latency         | < 10ms      |

### Roadmap

#### Q1 2026

- ✅ OpenAI Integration
- ✅ Multi-provider support
- ✅ Enhanced error handling

#### Q2 2026

- [ ] Pattern library expansion
- [ ] Advanced visualization
- [ ] Batch processing

#### Q3 2026

- [ ] Multi-user collaboration
- [ ] Custom agent plugins
- [ ] Integration with EDA tools

#### Q4 2026

- [ ] Cloud-native deployment
- [ ] Advanced analytics
- [ ] Mobile app

### Acknowledgments

- **Groq** - Fast LLM inference
- **OpenAI** - High-quality language models
- **FastAPI** - Modern web framework
- **React** - UI framework
- **MongoDB** - Database
- **All Contributors** - Community support

### Contact

- **Website**: https://your-domain.com
- **Email**: support@your-domain.com
- **GitHub**: https://github.com/your-org/sva-chatbot
- **Documentation**: https://docs.your-domain.com

---

**Last Updated:** February 3, 2026  
**Version:** 2.0.0  
**Status:** Production Ready
