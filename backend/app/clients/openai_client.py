"""
OpenAI API client for LLM interactions

This client handles all communication with the OpenAI API, including:
- Chat completions with model fallback
- Token usage tracking
- Request/response logging
- Error handling and retries
- Response caching for common requests
- Performance metrics tracking

Mirrors GroqClient interface for drop-in compatibility.
"""
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI
from ..config import settings
from ..utils.cache import llm_cache, generate_cache_key
from ..utils.metrics import track_llm_request
from ..utils.structured_logging import log_llm_request
from .base import LLMAPIError

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Async client for OpenAI API interactions
    
    Mirrors GroqClient interface for drop-in compatibility with existing agents.
    Supports async/await patterns, response caching, token tracking, and automatic
    model fallback for resilience.
    
    Validates: Requirements 1.1, 1.8
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI API client
        
        Creates an AsyncOpenAI client instance and sets up model configuration
        and token usage tracking.
        
        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        
        Validates: Requirements 1.1, 1.8
        """
        self.api_key = api_key or settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.primary_model = settings.openai_primary_model
        self.fallback_model = settings.openai_fallback_model
        self._token_usage = {}  # Track token usage per project
        
        logger.info(
            f"OpenAI client initialized with primary_model={self.primary_model}, "
            f"fallback_model={self.fallback_model}"
        )
    
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
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to primary model)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            project_id: Project ID for token tracking
            use_fallback: Whether to use fallback model
            use_cache: Whether to use response caching (default: True)
            
        Returns:
            API response dict in standardized format:
            {
                "id": str,
                "model": str,
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": str
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
            
        Raises:
            LLMAPIError: If API call fails
            
        Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 10.1, 10.4, 11.1, 11.3, 11.4
        """
        # Select model
        if model is None:
            model = self.fallback_model if use_fallback else self.primary_model
        
        # Check cache if enabled
        if use_cache:
            cache_key = self._generate_llm_cache_key(
                messages, model, temperature, max_tokens, top_p
            )
            cached_response = llm_cache.get(cache_key)
            if cached_response is not None:
                logger.info(f"Using cached LLM response for model={model}")
                return cached_response
        
        # Log request
        logger.info(
            f"OpenAI API request: model={model}, messages={len(messages)}, "
            f"temp={temperature}, max_tokens={max_tokens}"
        )
        
        start_time = time.time()
        
        try:
            # Make API call to OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Convert response to dict format matching GroqClient
            result = {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            # Track token usage
            usage = result.get("usage", {})
            if project_id and usage:
                self._track_token_usage(project_id, usage)
            
            # Track metrics
            track_llm_request(model, duration)
            
            # Log with structured logging
            log_llm_request(
                model=model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                duration=duration,
                success=True,
                project_id=project_id,
                provider="openai"
            )
            
            # Cache response if enabled
            if use_cache:
                llm_cache.set(cache_key, result, ttl=1800)  # 30 minutes
            
            # Log response
            logger.info(
                f"OpenAI API response: model={model}, "
                f"tokens={usage.get('total_tokens', 'unknown')}, "
                f"duration={duration:.3f}s"
            )
            
            return result
            
        except Exception as e:
            # Calculate duration for failed request
            duration = time.time() - start_time
            
            # Determine error type and message
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Extract status code if available
            status_code = getattr(e, 'status_code', None)
            
            logger.error(
                f"OpenAI API error: {error_type}: {error_msg}",
                extra={
                    "provider": "openai",
                    "error_type": error_type,
                    "status_code": status_code,
                    "model": model,
                    "project_id": project_id,
                    "duration": duration
                }
            )
            
            # Track failed request
            track_llm_request(model, duration)
            log_llm_request(
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                duration=duration,
                success=False,
                project_id=project_id,
                provider="openai"
            )
            
            # Raise standardized error
            raise LLMAPIError(
                message=f"{error_type}: {error_msg}",
                provider="openai",
                status_code=status_code,
                original_error=e
            )
    
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
        Make chat completion request with automatic fallback to secondary model
        
        Tries primary model first, falls back to secondary model on failure.
        With aggressive fallback, uses fallback model on rate limit errors immediately.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            project_id: Project ID for token tracking
            use_cache: Whether to use response caching
            use_aggressive_fallback: Use fallback model on rate limits immediately
            
        Returns:
            API response dict in standardized format
            
        Raises:
            LLMAPIError: If both primary and fallback models fail
            
        Validates: Requirements 2.1, 2.2, 2.3, 2.4
        """
        try:
            # Try primary model first
            logger.info(f"Attempting OpenAI API call with primary model: {self.primary_model}")
            return await self.chat_completion(
                messages=messages,
                model=self.primary_model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                project_id=project_id,
                use_fallback=False,
                use_cache=use_cache
            )
        except LLMAPIError as e:
            error_str = str(e)
            
            # Check if it's a rate limit error and aggressive fallback is enabled
            is_rate_limit = (
                "rate limit" in error_str.lower() or 
                "429" in error_str or
                e.status_code == 429
            )
            
            if use_aggressive_fallback and is_rate_limit:
                logger.warning(
                    f"Rate limit hit on {self.primary_model}. "
                    f"Using aggressive fallback to {self.fallback_model} immediately"
                )
            else:
                logger.warning(
                    f"Primary model {self.primary_model} failed: {str(e)}. "
                    f"Falling back to {self.fallback_model}"
                )
            
            # Fall back to secondary model
            return await self.chat_completion(
                messages=messages,
                model=self.fallback_model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                project_id=project_id,
                use_fallback=True,
                use_cache=use_cache
            )
    
    def _generate_llm_cache_key(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> str:
        """
        Generate cache key for LLM request
        
        Args:
            messages: List of message dicts
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            top_p: Top-p parameter
            
        Returns:
            Cache key string
        """
        return generate_cache_key(
            model=model,
            messages=str(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
    
    def _track_token_usage(self, project_id: str, usage: Dict[str, int]) -> None:
        """
        Track token usage per project
        
        Accumulates token counts across all API calls for a given project.
        
        Args:
            project_id: Project ID
            usage: Usage dict from API response
            
        Validates: Requirements 10.1, 10.2, 10.3
        """
        if project_id not in self._token_usage:
            self._token_usage[project_id] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "requests": 0
            }
        
        self._token_usage[project_id]["prompt_tokens"] += usage.get("prompt_tokens", 0)
        self._token_usage[project_id]["completion_tokens"] += usage.get("completion_tokens", 0)
        self._token_usage[project_id]["total_tokens"] += usage.get("total_tokens", 0)
        self._token_usage[project_id]["requests"] += 1
        
        logger.info(
            f"Token usage for project {project_id}: "
            f"total={self._token_usage[project_id]['total_tokens']}, "
            f"requests={self._token_usage[project_id]['requests']}"
        )
    
    def get_token_usage(self, project_id: str) -> Dict[str, int]:
        """
        Get token usage statistics for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with token usage statistics:
            {
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int,
                "requests": int
            }
            
        Validates: Requirements 10.2, 10.3
        """
        return self._token_usage.get(project_id, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "requests": 0
        })
    
    async def close(self) -> None:
        """
        Close the OpenAI client session and cleanup resources
        
        Properly releases network connections and cleans up the AsyncOpenAI client.
        This method is idempotent - calling multiple times is safe.
        
        Validates: Requirements 1.8
        """
        if self.client:
            await self.client.close()
            logger.info("OpenAI API client session closed")
    
    async def __aenter__(self):
        """
        Async context manager entry
        
        Enables usage with async with statement:
            async with OpenAIClient() as client:
                response = await client.chat_completion(...)
        
        Returns:
            self for use in context
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit
        
        Automatically closes the client when exiting the context.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.close()
