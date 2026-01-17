# Backend Setup Guide

## Installation

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set:
# - MONGODB_URL (default: mongodb://localhost:27017)
# - GROQ_API_KEY (your Groq API key)
# - JWT_SECRET_KEY (generate a secure random string)
```

### 3. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Or using docker-compose from project root
docker-compose up -d mongodb
```

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run property tests only
pytest tests/test_database_properties.py -v

# Run property tests with more iterations
pytest tests/test_database_properties.py -v --hypothesis-seed=random
```

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Database Collections

The following MongoDB collections are automatically created with indexes:

1. **projects** - User projects with metadata
2. **specifications** - Uploaded specification documents
3. **rtl_designs** - RTL design files and analysis
4. **assertions** - Generated SVA assertions
5. **pattern_library** - Reusable assertion patterns

## Testing

### Property-Based Tests

The system includes property-based tests using Hypothesis that run 100 iterations by default:

- **Property 30**: Project Metadata Persistence
- **Property 44**: Database Storage Consistency

These tests validate that data round-trips correctly through the database.

### Running Property Tests

```bash
# Run with default 100 iterations
pytest tests/test_database_properties.py

# Run with more iterations for thorough testing
pytest tests/test_database_properties.py --hypothesis-profile=thorough
```

## Troubleshooting

### MongoDB Connection Issues

If you see "Database not connected" errors:

1. Ensure MongoDB is running: `docker ps` or check local MongoDB service
2. Verify MONGODB_URL in .env matches your MongoDB instance
3. Check MongoDB logs for connection errors

### Import Errors

If you see module import errors:

1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (requires 3.10+)

### Test Failures

If property tests fail:

1. Ensure MongoDB test database is accessible
2. Check that no other tests are running concurrently
3. Review the failing example provided by Hypothesis
