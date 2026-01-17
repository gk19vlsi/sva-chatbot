# SVA-Chatbot Backend

FastAPI-based backend for the SVA-Chatbot system.

## Setup

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using Poetry

```bash
# Install dependencies
poetry install

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   ├── database.py      # MongoDB connection
│   ├── models/          # Pydantic models
│   ├── routes/          # API endpoints
│   ├── agents/          # AI agent implementations
│   └── utils/           # Utility functions
├── tests/               # Test files
├── requirements.txt     # Pip dependencies
├── pyproject.toml       # Poetry configuration
└── .env.example         # Environment template
```
