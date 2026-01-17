# SVA-Chatbot Developer Documentation

Complete developer guide for contributing to and extending the SVA-Chatbot system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent System](#agent-system)
3. [Database Schema](#database-schema)
4. [Development Setup](#development-setup)
5. [Testing](#testing)
6. [Contributing](#contributing)
7. [Code Style](#code-style)

## Architecture Overview

### System Architecture

SVA-Chatbot follows a three-tier architecture:

```
┌─────────────────────────────────────────┐
│         Frontend (React + TypeScript)    │
│  - File Upload UI                        │
│  - Real-time Monitoring                  │
│  - Assertion Viewer                      │
└──────────────┬──────────────────────────┘
               │ REST API / WebSocket
┌──────────────┴──────────────────────────┐
│         Backend (FastAPI + Python)       │
│  ┌────────────────────────────────────┐ │
│  │     Multi-Agent Pipeline           │ │
│  │  1. Specification Parser           │ │
│  │  2. RTL Analyzer                   │ │
│  │  3. Alignment Agent                │ │
│  │  4. SVA Generator                  │ │
│  │  5. Validation Agent               │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │     Groq API Integration           │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         MongoDB Database                 │
│  - Projects                              │
│  - Specifications                        │
│  - RTL Designs                           │
│  - Assertions                            │
│  - Pattern Library                       │
└─────────────────────────────────────────┘
```

### Technology Stack

**Backend:**

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Database**: MongoDB 7.0+ (Motor async driver)
- **LLM**: Groq API (llama-3.3-70b-versatile, mixtral-8x7b-32768)
- **Testing**: pytest, Hypothesis (property-based testing)

**Frontend:**

- **Framework**: React 18+
- **Language**: TypeScript 5+
- **Build Tool**: Vite
- **UI**: Tailwind CSS
- **Testing**: Vitest, React Testing Library

**Infrastructure:**

- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Railway, Render, or self-hosted

### Key Design Patterns

1. **Multi-Agent Pipeline**: Sequential processing with context passing
2. **Event-Driven**: WebSocket for real-time updates
3. **Repository Pattern**: Database abstraction
4. **Factory Pattern**: Agent initialization
5. **Strategy Pattern**: LLM model fallback

## Agent System

### Agent Architecture

All agents inherit from the `Agent` base class:

```python
from abc import ABC, abstractmethod
from app.agents.base import Agent, AgentResult, PipelineContext

class MyAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        # Agent implementation
        pass
```

### Agent Base Class

**Location**: `backend/app/agents/base.py`

**Key Methods:**

- `execute()`: Main agent logic (abstract, must implement)
- `call_groq()`: LLM API call with retry and fallback
- `_log_execution()`: Performance tracking

**Example:**

```python
class SpecificationParserAgent(Agent):
    async def execute(self, context: PipelineContext) -> AgentResult:
        start_time = datetime.utcnow()

        try:
            # Load specifications
            specs = await self._load_specifications(context)

            # Process with LLM
            requirements = await self._parse_requirements(specs)

            # Store results
            await self._store_requirements(context, requirements)

            # Return success
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={"requirements": requirements},
                execution_time=self._calculate_execution_time(start_time)
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(e),
                execution_time=self._calculate_execution_time(start_time)
            )
```

### Pipeline Context

Context is passed between agents:

```python
class PipelineContext(BaseModel):
    project_id: str
    data: Dict[str, Any] = {}
```

Agents can:

- Read data from previous agents
- Add data for subsequent agents
- Access project information

### Creating a New Agent

1. **Create agent file**: `backend/app/agents/my_agent.py`

```python
from app.agents.base import Agent, AgentResult, PipelineContext

class MyAgent(Agent):
    """
    Description of what this agent does

    Validates: Requirements X.Y, Z.W
    """

    async def execute(self, context: PipelineContext) -> AgentResult:
        # Implementation
        pass
```

2. **Register in orchestrator**: `backend/app/agents/orchestrator.py`

```python
def _initialize_agents(self):
    return {
        'my_agent': MyAgent(self.groq_client, self.db),
        # ... other agents
    }
```

3. **Add to pipeline sequence**:

```python
async def execute_pipeline(self, project_id: str, websocket: WebSocket):
    # ... existing agents

    # Add your agent
    my_result = await self.agents['my_agent'].execute(context)
    await self._send_update(websocket, 'my_agent_completed', my_result)
```

### Agent Best Practices

**Do:**

- ✅ Use structured logging
- ✅ Track execution time
- ✅ Handle errors gracefully
- ✅ Validate inputs
- ✅ Document requirements
- ✅ Write property tests

**Don't:**

- ❌ Block on I/O operations
- ❌ Store state in agent instances
- ❌ Ignore errors
- ❌ Skip logging
- ❌ Hardcode values

## Database Schema

### Collections

#### Projects Collection

```python
{
    "_id": ObjectId,
    "name": str,
    "description": str,
    "created_at": datetime,
    "updated_at": datetime,
    "user_id": str,
    "status": "draft" | "processing" | "completed" | "failed",
    "metadata": {
        "total_specs": int,
        "total_rtl_files": int,
        "total_assertions": int
    }
}
```

**Indexes:**

- `(user_id, created_at)`
- `user_id`
- `status`

#### Specifications Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "filename": str,
    "file_type": "pdf" | "docx" | "md" | "txt",
    "file_path": str,
    "raw_text": str,
    "parsed_requirements": [
        {
            "requirement_id": str,
            "text": str,
            "category": str,
            "temporal_keywords": [str],
            "entities": [str]
        }
    ],
    "uploaded_at": datetime,
    "processed": bool
}
```

**Indexes:**

- `project_id`
- `(project_id, processed)`

#### RTL Designs Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "filename": str,
    "source_code": str,
    "parsed_ast": dict,
    "analysis": {
        "modules": [
            {
                "name": str,
                "ports": [dict],
                "signals": [dict],
                "clocks": [str],
                "resets": [str]
            }
        ]
    },
    "uploaded_at": datetime,
    "processed": bool
}
```

**Indexes:**

- `project_id`
- `(project_id, processed)`

#### Assertions Collection

```python
{
    "_id": ObjectId,
    "project_id": ObjectId,
    "requirement_id": str,
    "assertion_code": str,
    "assertion_type": "immediate" | "concurrent" | "property" | "sequence",
    "category": str,
    "confidence_score": float,
    "rtl_module": str,
    "explanation": str,
    "traceability": {
        "spec_reference": str,
        "requirement_text": str,
        "rtl_signals": [str],
        "line_numbers": [int]
    },
    "validation": {
        "syntax_valid": bool,
        "quality_score": float
    },
    "user_feedback": {
        "rating": int,
        "modified": bool,
        "comments": str
    },
    "generated_at": datetime
}
```

**Indexes:**

- `(project_id, confidence_score)`
- `requirement_id`
- `project_id`

### Database Operations

**Query Optimization:**

```python
from app.database import QueryOptimizer

# Use projections
assertions = await QueryOptimizer.get_assertions_by_project(
    db, project_id, limit=50, summary=True
)

# Use aggregation
project = await QueryOptimizer.get_project_with_stats(
    db, project_id, user_id
)
```

**Transactions:**

```python
async with await db.client.start_session() as session:
    async with session.start_transaction():
        # Multiple operations
        await db.projects.insert_one(project, session=session)
        await db.specifications.insert_one(spec, session=session)
```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Docker & Docker Compose

### Backend Setup

1. **Clone repository:**

```bash
git clone https://github.com/your-org/sva-chatbot.git
cd sva-chatbot/backend
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run development server:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend:**

```bash
cd frontend
```

2. **Install dependencies:**

```bash
npm install
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env if needed
```

4. **Run development server:**

```bash
npm run dev
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build

# Stop services
docker-compose down
```

## Testing

### Backend Testing

**Run all tests:**

```bash
cd backend
pytest tests/ -v
```

**Run with coverage:**

```bash
pytest tests/ --cov=app --cov-report=html
```

**Run specific test:**

```bash
pytest tests/test_agents.py::test_spec_parser -v
```

**Run property tests:**

```bash
pytest tests/test_*_properties.py -v
```

### Property-Based Testing

We use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1, max_size=100),
    description=st.text(max_size=500)
)
def test_project_round_trip(name, description):
    """
    Feature: sva-chatbot, Property 30: Project Metadata Persistence

    For any created project, storing it and then retrieving it
    should produce a project record with the same name, description, and user_id.
    """
    project_id = create_project(name, description, test_user_id)
    retrieved = get_project(project_id)

    assert retrieved["name"] == name
    assert retrieved["description"] == description
    assert retrieved["user_id"] == test_user_id
```

### Frontend Testing

**Run all tests:**

```bash
cd frontend
npm run test
```

**Run with coverage:**

```bash
npm run test -- --coverage
```

**Run specific test:**

```bash
npm run test -- FileUpload.test.tsx
```

### Integration Testing

```python
async def test_complete_pipeline():
    """Test the entire generation pipeline"""
    # Create project
    project_id = await create_project("Test Project")

    # Upload files
    await upload_specification(project_id, "spec.pdf")
    await upload_rtl(project_id, "design.sv")

    # Start generation
    async with websocket_connect(f"/ws/generation?project={project_id}") as ws:
        await trigger_generation(project_id)

        # Collect updates
        updates = []
        async for message in ws:
            updates.append(message)
            if message["status"] == "completed":
                break

        # Verify pipeline executed
        assert any(u["agent"] == "spec_parser" for u in updates)
        assert any(u["agent"] == "sva_generator" for u in updates)

    # Verify assertions created
    assertions = await get_assertions(project_id)
    assert len(assertions) > 0
```

## Contributing

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make your changes**
4. **Write tests**
5. **Run tests**: `pytest` and `npm test`
6. **Commit**: `git commit -m "Add my feature"`
7. **Push**: `git push origin feature/my-feature`
8. **Create Pull Request**

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG.md**
5. **Request review** from maintainers

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Example:**

```
feat(agents): Add new validation agent

Implement validation agent that checks assertion quality
and detects vacuity issues.

Closes #123
```

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

**Imports:**

```python
# Standard library
import os
import sys

# Third-party
from fastapi import FastAPI
import numpy as np

# Local
from app.agents import Agent
from app.utils import helper
```

**Type Hints:**

```python
def process_data(data: List[Dict[str, Any]]) -> Optional[str]:
    """Process data and return result"""
    pass
```

**Docstrings:**

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

**Linting:**

```bash
# Format code
black app/

# Check style
flake8 app/

# Type checking
mypy app/
```

### TypeScript Style Guide

Follow Airbnb style guide with these additions:

**Interfaces:**

```typescript
interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
}
```

**Components:**

```typescript
interface Props {
  project: Project;
  onUpdate: (project: Project) => void;
}

export const ProjectCard: React.FC<Props> = ({ project, onUpdate }) => {
  // Component implementation
};
```

**Linting:**

```bash
# Check style
npm run lint

# Fix issues
npm run lint -- --fix
```

### Documentation Style

**Code Comments:**

- Explain WHY, not WHAT
- Keep comments up-to-date
- Use TODO for future work

**API Documentation:**

- Document all endpoints
- Include request/response examples
- Specify authentication requirements

**User Documentation:**

- Use clear, simple language
- Include screenshots
- Provide examples

## Additional Resources

### Internal Documentation

- [API Documentation](API.md)
- [User Guide](USER_GUIDE.md)
- [Deployment Guide](../DEPLOYMENT.md)
- [Performance Optimizations](../backend/PERFORMANCE_OPTIMIZATIONS.md)
- [Monitoring & Logging](../backend/MONITORING_LOGGING.md)

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [SystemVerilog LRM](https://ieeexplore.ieee.org/document/8299595)
- [Groq API Documentation](https://console.groq.com/docs)

### Community

- **GitHub**: https://github.com/your-org/sva-chatbot
- **Discussions**: https://github.com/your-org/sva-chatbot/discussions
- **Issues**: https://github.com/your-org/sva-chatbot/issues
- **Email**: dev@your-domain.com

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Version**: 1.0.0  
**Last Updated**: January 17, 2026  
**Maintainers**: dev-team@your-domain.com
