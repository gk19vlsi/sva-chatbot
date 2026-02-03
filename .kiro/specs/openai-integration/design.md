# Design Document: OpenAI Integration

## Overview

This design document describes the architecture for adding OpenAI API support to the SVA-Chatbot project. The solution introduces a unified client interface, a factory pattern for client creation, and an OpenAI client implementation that mirrors the existing GroqClient functionality. The design maintains full backward compatibility while enabling seamless switching between LLM providers through configuration.

The key architectural principle is abstraction: agents interact with a common client interface without knowing which provider is being used. This allows for easy provider switching, testing, and future extensibility to additional providers.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Agents Layer                         │
│  (Orchestrator, SVAGenerator, RTLAnalyzer, etc.)            │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLMClientFactory                          │
│              (Creates appropriate client)                    │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    Creates  │                                │ Creates
             ▼                                ▼
┌─────────────────────┐          ┌─────────────────────────┐
│    GroqClient       │          │    OpenAIClient         │
│  (Existing)         │          │    (New)                │
└─────────────────────┘          └─────────────────────────┘
             │                                │
             │ Calls                          │ Calls
             ▼                                ▼
┌─────────────────────┐          ┌─────────────────────────┐
│   Groq API          │          │   OpenAI API            │
└─────────────────────┘          └─────────────────────────┘
```

### Design Patterns

1. **Factory Pattern**: `LLMClientFactory` creates the appropriate client based on configuration
2. **Strategy Pattern**: Different client implementations (Groq, OpenAI) provide the same interface
3. **Dependency Injection**: Agents receive clients through constructor injection
4. **Adapter Pattern**: Both clients adapt their respective APIs to a common interface

### Configuration Flow

```
.env file → Settings (Pydantic) → LLMClientFactory → Client Instance → Agents
```

## Components and Interfaces

### 1. Base Client Interface (Protocol)

We'll define a Protocol class that both GroqClient and OpenAIClient will implement. This ensures type safety and a common interface.

```python
from typing import Protocol, List, Dict, Optional, Any
from typing_extensions import runtime_checkable

@runtime_checkable
class LLMClient(Protocol):
    """Protocol defining the interface for LLM clients"""

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

### 2. OpenAI Client Implementation

The OpenAI client will mirror the GroqClient structure but use the OpenAI Python SDK.

**Key Responsibilities:**

- Manage OpenAI API authentication
- Handle chat completion requests
- Implement model fallback logic
- Track token usage per project
- Cache responses
- Log requests and responses
- Handle errors and retries

**Implementation Details:**

```python
from openai import AsyncOpenAI
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

class OpenAIClient:
    """
    Async client for OpenAI API interactions

    Mirrors GroqClient interface for drop-in compatibility.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI API client

        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        """
        self.api_key = api_key or settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.primary_model = settings.openai_primary_model
        self.fallback_model = settings.openai_fallback_model
        self._token_usage = {}  # Track token usage per project

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
        """
        Make chat completion request to OpenAI API with optional caching

        Implementation follows GroqClient pattern:
        1. Check cache if enabled
        2. Make API request
        3. Track token usage
        4. Log metrics
        5. Cache response
        6. Return standardized response format
        """
        # Implementation details...

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
        """
        Make chat completion request with automatic fallback

        Tries primary model first, falls back to secondary on failure.
        """
        # Implementation details...
```

### 3. LLM Client Factory

The factory creates and configures the appropriate client based on settings.

```python
from typing import Union
from app.config import settings
from app.clients.groq_client import GroqClient
from app.clients.openai_client import OpenAIClient

class LLMClientFactory:
    """
    Factory for creating LLM clients based on configuration

    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """

    @staticmethod
    def create_client() -> Union[GroqClient, OpenAIClient]:
        """
        Create and return the configured LLM client

        Returns:
            GroqClient or OpenAIClient based on settings.llm_provider

        Raises:
            ValueError: If provider is invalid or required config is missing
        """
        provider = settings.llm_provider.lower()

        if provider == "groq":
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY is required when using Groq provider")
            return GroqClient(api_key=settings.groq_api_key)

        elif provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return OpenAIClient(api_key=settings.openai_api_key)

        else:
            raise ValueError(
                f"Invalid LLM provider: {provider}. "
                f"Must be 'groq' or 'openai'"
            )

    @staticmethod
    def get_provider_name() -> str:
        """Get the name of the configured provider"""
        return settings.llm_provider
```

### 4. Configuration Updates

Extend the Settings class to include OpenAI configuration:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "sva_chatbot"

    # LLM Provider Selection
    llm_provider: str = "groq"  # "groq" or "openai"

    # Groq API Configuration
    groq_api_key: str = ""
    groq_primary_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"

    # OpenAI API Configuration
    openai_api_key: str = ""
    openai_primary_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # ... rest of configuration ...
```

### 5. Agent Integration Pattern

Agents will be updated to use the factory:

```python
from app.clients.factory import LLMClientFactory

class Orchestrator:
    """Orchestrator for Multi-Agent Pipeline"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize orchestrator and all agents

        Args:
            db: MongoDB database instance
        """
        # Create LLM client using factory
        self.llm_client = LLMClientFactory.create_client()
        self.db = db

        # Initialize all five agents with the client
        self.agents: Dict[str, Agent] = {
            "spec_parser": SpecificationParserAgent(self.llm_client, db),
            "rtl_analyzer": RTLAnalyzerAgent(self.llm_client, db),
            "alignment": AlignmentAgent(self.llm_client, db),
            "sva_generator": SVAGeneratorAgent(self.llm_client, db),
            "validation": ValidationAgent(self.llm_client, db)
        }

        logger.info(f"Orchestrator initialized with {LLMClientFactory.get_provider_name()} provider")
```

## Data Models

### Response Format Standardization

Both clients will return responses in a standardized format:

```python
{
    "id": str,  # Response ID
    "model": str,  # Model used
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": str  # Generated text
            },
            "finish_reason": str
        }
    ],
    "usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
    }
}
```

### Token Usage Tracking

```python
{
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int,
    "requests": int
}
```

### Error Response Format

```python
class LLMAPIError(Exception):
    """Base exception for LLM API errors"""

    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Response Format Consistency

_For any_ successful chat completion request made through OpenAI_Client, the response format SHALL match the format returned by GroqClient, including the same fields (id, model, choices, usage) and data types.

**Validates: Requirements 1.3**

### Property 2: API Call Correctness

_For any_ chat completion request with valid parameters, the OpenAI_Client SHALL make a properly formatted API call to OpenAI's chat completion endpoint with all required fields (model, messages, temperature, max_tokens, top_p).

**Validates: Requirements 1.2**

### Property 3: Error Handling

_For any_ API call that fails (network error, authentication error, rate limit, invalid model), the OpenAI_Client SHALL raise an LLMAPIError with a descriptive message that includes the error type and provider name.

**Validates: Requirements 1.4, 9.1, 9.2, 9.3**

### Property 4: Token Usage Tracking

_For any_ sequence of API calls with the same project_id, the OpenAI_Client SHALL accumulate token counts (prompt_tokens, completion_tokens, total_tokens) such that the total equals the sum of all individual call usages, and the get_token_usage method SHALL return these accumulated values.

**Validates: Requirements 1.5, 10.1, 10.2, 10.3**

### Property 5: Response Caching

_For any_ chat completion request with use_cache=True, making the same request twice within the TTL period SHALL return the cached response on the second call without making an additional API call.

**Validates: Requirements 1.6**

### Property 6: Request and Response Logging

_For any_ chat completion request (successful or failed), the OpenAI_Client SHALL log structured information including the provider name, model, request parameters, response status, token usage, and execution duration.

**Validates: Requirements 1.7, 10.4, 11.4**

### Property 7: Model Fallback Behavior

_For any_ chat completion request where the primary model fails (API error, rate limit, or unavailable), the chat_completion_with_fallback method SHALL automatically retry with the fallback model and log the fallback attempt with the failure reason.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 8: Configuration Validation

_For any_ invalid configuration (invalid LLM_PROVIDER value, missing API key for selected provider, or unsupported provider name), the Client_Factory SHALL raise a ValueError with a clear message indicating the configuration problem.

**Validates: Requirements 3.1, 3.5, 4.3**

### Property 9: Provider Switching

_For any_ agent operation (spec parsing, RTL analysis, alignment, SVA generation, validation), switching the LLM_PROVIDER configuration between "groq" and "openai" SHALL allow the operation to complete successfully with either provider without code changes.

**Validates: Requirements 5.3**

### Property 10: Backward Compatibility

_For any_ system operation that worked with Groq-only configuration before the update, the same operation SHALL continue to work identically when LLM_PROVIDER is set to "groq" or omitted (defaulting to "groq").

**Validates: Requirements 8.1, 8.2, 8.4**

### Property 11: Performance Metrics Tracking

_For any_ API call made through OpenAI_Client, the client SHALL track and report request duration, success/failure status to the existing metrics system, and log performance data with the provider name for filtering.

**Validates: Requirements 11.1, 11.2, 11.3, 11.4**

## Error Handling

### Error Types and Handling Strategy

1. **Authentication Errors**
   - Cause: Invalid or missing API key
   - Handling: Raise `LLMAPIError` with clear message indicating which provider's key is invalid
   - Logging: Log error with provider name and error type
   - User Action: Update API key in .env file

2. **Rate Limit Errors**
   - Cause: Exceeded API rate limits
   - Handling: Automatic fallback to secondary model if aggressive_fallback enabled
   - Logging: Log rate limit hit and fallback attempt
   - User Action: Wait or upgrade API plan

3. **Model Unavailable Errors**
   - Cause: Requested model doesn't exist or is unavailable
   - Handling: Fallback to secondary model, raise error if both fail
   - Logging: Log which provider and model were requested
   - User Action: Update model configuration

4. **Network Errors**
   - Cause: Connection timeout, DNS failure, etc.
   - Handling: Retry with exponential backoff (up to 3 attempts)
   - Logging: Log network error details
   - User Action: Check network connectivity

5. **Configuration Errors**
   - Cause: Invalid provider name, missing required settings
   - Handling: Raise `ValueError` at startup before any API calls
   - Logging: Log configuration validation failure
   - User Action: Fix .env configuration

6. **Response Parsing Errors**
   - Cause: Unexpected API response format
   - Handling: Log raw response, raise `LLMAPIError`
   - Logging: Log full response for debugging
   - User Action: Report issue, may indicate API changes

### Error Response Format

All errors will use a consistent format:

```python
class LLMAPIError(Exception):
    """Exception for LLM API errors"""

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
        super().__init__(f"[{provider}] {message}")
```

### Logging Strategy

All errors will be logged with structured data:

```python
logger.error(
    f"LLM API error",
    extra={
        "provider": provider,
        "error_type": error_type,
        "status_code": status_code,
        "model": model,
        "project_id": project_id,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:

- Specific configuration examples (Groq-only, OpenAI-only, switching providers)
- Edge cases (missing API keys, invalid provider names)
- Integration points (factory creation, agent initialization)
- File content verification (.env.example, requirements.txt)

**Property-Based Tests** focus on:

- Response format consistency across random inputs
- Token tracking accuracy across random API call sequences
- Caching behavior with random request patterns
- Error handling across random failure scenarios
- Fallback behavior with random error conditions
- Provider switching with random agent operations

### Property-Based Testing Configuration

We'll use **Hypothesis** (already in requirements.txt) for property-based testing:

- **Minimum 100 iterations** per property test
- Each test tagged with: **Feature: openai-integration, Property {number}: {property_text}**
- Tests will generate random:
  - Message lists (varying lengths, content)
  - Model parameters (temperature, max_tokens, top_p)
  - Project IDs
  - API responses (success and failure scenarios)
  - Configuration combinations

### Test Organization

```
backend/tests/
├── unit/
│   ├── test_openai_client.py          # Unit tests for OpenAI client
│   ├── test_llm_factory.py            # Unit tests for factory
│   ├── test_config_openai.py          # Unit tests for configuration
│   └── test_agent_integration.py      # Unit tests for agent integration
├── property/
│   ├── test_client_properties.py      # Property tests for client behavior
│   ├── test_factory_properties.py     # Property tests for factory
│   └── test_compatibility_properties.py  # Property tests for backward compatibility
└── integration/
    └── test_end_to_end_openai.py      # Integration tests with mocked APIs
```

### Mock Strategy

For testing without actual API calls:

- Mock OpenAI API responses using `unittest.mock` or `pytest-mock`
- Create fixtures for common response patterns
- Simulate various error conditions
- Test both providers with identical mock data to verify consistency

### Example Property Test Structure

```python
from hypothesis import given, strategies as st
import pytest

@given(
    messages=st.lists(
        st.fixed_dictionaries({
            'role': st.sampled_from(['user', 'assistant', 'system']),
            'content': st.text(min_size=1, max_size=1000)
        }),
        min_size=1,
        max_size=10
    ),
    temperature=st.floats(min_value=0.0, max_value=2.0),
    max_tokens=st.integers(min_value=1, max_value=4096)
)
@pytest.mark.property_test
async def test_response_format_consistency(messages, temperature, max_tokens):
    """
    Feature: openai-integration, Property 1: Response Format Consistency

    For any successful chat completion request, OpenAI_Client response format
    SHALL match GroqClient response format.
    """
    # Test implementation...
```

### Coverage Goals

- **Line Coverage**: Minimum 90% for new code
- **Branch Coverage**: Minimum 85% for error handling paths
- **Property Coverage**: All 11 correctness properties must have corresponding property tests
- **Integration Coverage**: All agents must be tested with both providers

### Continuous Integration

Tests will run in CI/CD pipeline:

1. Unit tests run on every commit
2. Property tests run on every PR
3. Integration tests run before merge to main
4. Coverage reports generated and tracked
5. Tests must pass with both mocked Groq and OpenAI clients
