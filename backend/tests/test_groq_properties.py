"""
Property-based tests for Groq API client

These tests validate universal correctness properties for LLM integration.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from app.clients.groq_client import GroqClient, GroqAPIError
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

# Suppress function_scoped_fixture health check
settings.register_profile("default", suppress_health_check=[HealthCheck.function_scoped_fixture])
settings.load_profile("default")


@pytest.mark.asyncio
@given(
    prompt_tokens=st.integers(min_value=10, max_value=1000),
    completion_tokens=st.integers(min_value=10, max_value=500)
)
@settings(max_examples=10)
async def test_property_42_token_usage_tracking(prompt_tokens, completion_tokens):
    """
    Feature: sva-chatbot, Property 42: Token Usage Tracking
    
    For any Groq API call, the system should record the token count
    and associate it with the project.
    
    Validates: Requirements 17.3
    """
    project_id = "test_project_123"
    
    # Mock the API response
    mock_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "llama-3.3-70b-versatile",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Test response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    }
    
    # Mock the aiohttp.ClientSession at the module level
    with patch('app.clients.groq_client.aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="")
        mock_session.post.return_value = mock_context
        mock_session.closed = False
        mock_session.close = AsyncMock()
        
        client = GroqClient(api_key="test_key")
        
        try:
            # Make API call
            messages = [{"role": "user", "content": "Test"}]
            result = await client.chat_completion(
                messages=messages,
                project_id=project_id
            )
            
            # Verify token usage was tracked
            usage = client.get_token_usage(project_id)
            
            assert usage["prompt_tokens"] == prompt_tokens, \
                f"Prompt tokens should be tracked correctly"
            assert usage["completion_tokens"] == completion_tokens, \
                f"Completion tokens should be tracked correctly"
            assert usage["total_tokens"] == prompt_tokens + completion_tokens, \
                f"Total tokens should be sum of prompt and completion"
            assert usage["requests"] == 1, \
                f"Request count should be incremented"
            
            # Make another call to verify accumulation
            result = await client.chat_completion(
                messages=messages,
                project_id=project_id
            )
            
            usage = client.get_token_usage(project_id)
            assert usage["total_tokens"] == 2 * (prompt_tokens + completion_tokens), \
                f"Token usage should accumulate across requests"
            assert usage["requests"] == 2, \
                f"Request count should accumulate"
        
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_property_41_llm_model_fallback():
    """
    Feature: sva-chatbot, Property 41: LLM Model Fallback
    
    For any Groq API call that fails with the primary model (llama-3.3-70b-versatile),
    the system should retry with the fallback model (mixtral-8x7b-32768).
    
    Validates: Requirements 17.1, 17.2
    """
    # Mock responses
    fallback_success_response = {
        "id": "chatcmpl-456",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "mixtral-8x7b-32768",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Fallback response"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }
    
    # Track which models were called
    models_called = []
    
    async def mock_post(url, **kwargs):
        # Determine which model is being called based on payload
        model = kwargs.get('json', {}).get('model', '')
        models_called.append(model)
        
        mock_context = AsyncMock()
        
        if model == "llama-3.3-70b-versatile":
            # Primary model fails
            mock_context.__aenter__.return_value.status = 500
            mock_context.__aenter__.return_value.text = AsyncMock(return_value="Primary model error")
            mock_context.__aenter__.return_value.json = AsyncMock(side_effect=Exception("Error"))
        else:
            # Fallback model succeeds
            mock_context.__aenter__.return_value.status = 200
            mock_context.__aenter__.return_value.json = AsyncMock(return_value=fallback_success_response)
            mock_context.__aenter__.return_value.text = AsyncMock(return_value="")
        
        return mock_context
    
    # Mock the aiohttp.ClientSession at the module level
    with patch('app.clients.groq_client.aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        mock_session.post = mock_post
        mock_session.closed = False
        mock_session.close = AsyncMock()
        
        client = GroqClient(api_key="test_key")
        
        try:
            # Make API call with fallback
            messages = [{"role": "user", "content": "Test"}]
            result = await client.chat_completion_with_fallback(messages=messages)
            
            # Verify fallback occurred
            assert len(models_called) == 2, \
                "Should have called both primary and fallback models"
            assert models_called[0] == client.primary_model, \
                "Should try primary model first"
            assert models_called[1] == client.fallback_model, \
                "Should fall back to secondary model"
            assert result["model"] == client.fallback_model, \
                "Final response should be from fallback model"
        
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_groq_client_basic_functionality():
    """
    Test basic Groq client functionality with mocked responses
    """
    # Mock successful response
    mock_response = {
        "id": "chatcmpl-789",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "llama-3.3-70b-versatile",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40
        }
    }
    
    # Mock the aiohttp.ClientSession at the module level
    with patch('app.clients.groq_client.aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_response_obj.text = AsyncMock(return_value="")
        
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=mock_context)
        mock_session.closed = False
        mock_session.close = AsyncMock()
        
        client = GroqClient(api_key="test_key")
        
        try:
            # Make API call
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
            result = await client.chat_completion(messages=messages)
            
            # Verify response
            assert result["id"] == "chatcmpl-789"
            assert result["model"] == "llama-3.3-70b-versatile"
            assert len(result["choices"]) == 1
            assert result["choices"][0]["message"]["content"] == "Hello! How can I help you?"
        
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_groq_client_error_handling():
    """
    Test that Groq client properly handles API errors
    """
    # Mock the aiohttp.ClientSession at the module level
    with patch('app.clients.groq_client.aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session
        
        # Mock error response
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 401
        mock_context.__aenter__.return_value.text = AsyncMock(return_value="Unauthorized")
        mock_session.post.return_value = mock_context
        mock_session.closed = False
        mock_session.close = AsyncMock()
        
        client = GroqClient(api_key="test_key")
        
        try:
            # Make API call - should raise error
            messages = [{"role": "user", "content": "Test"}]
            
            with pytest.raises(GroqAPIError) as exc_info:
                await client.chat_completion(messages=messages)
            
            assert "401" in str(exc_info.value)
        
        finally:
            await client.close()
