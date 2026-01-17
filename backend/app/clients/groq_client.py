"""
Groq API client for LLM interactions

This client handles all communication with the Groq API, including:
- Chat completions with model fallback
- Token usage tracking
- Request/response logging
- Error handling and retries
- Response caching for common requests
- Performance metrics tracking
"""
import aiohttp
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from ..config import settings
from ..utils.cache import llm_cache, generate_cache_key
from ..utils.metrics import track_llm_request
from ..utils.structured_logging import log_llm_request

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Exception raised for Groq API errors"""
    pass


class GroqClient:
    """
    Async client for Groq API interactions
    
    Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq API client
        
        Args:
            api_key: Groq API key (defaults to settings.groq_api_key)
        """
        self.api_key = api_key or settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.primary_model = settings.groq_primary_model
        self.fallback_model = settings.groq_fallback_model
        self.session: Optional[aiohttp.ClientSession] = None
        self._token_usage = {}  # Track token usage per project
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
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
    ) -> Dict:
        """
        Make chat completion request to Groq API with optional caching
        
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
            API response dict
            
        Raises:
            GroqAPIError: If API call fails
            
        Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5
        """
        await self._ensure_session()
        
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
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        # Log request
        logger.info(f"Groq API request: model={model}, messages={len(messages)}, temp={temperature}")
        
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_text = await response.text()
                
                # Calculate duration
                duration = time.time() - start_time
                
                if response.status != 200:
                    error_msg = f"Groq API call failed (status {response.status}): {response_text}"
                    logger.error(error_msg)
                    
                    # Track failed request
                    track_llm_request(model, duration)
                    log_llm_request(
                        model=model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        duration=duration,
                        success=False,
                        project_id=project_id
                    )
                    
                    raise GroqAPIError(error_msg)
                
                result = await response.json()
                
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
                    project_id=project_id
                )
                
                # Cache response if enabled
                if use_cache:
                    llm_cache.set(cache_key, result, ttl=1800)  # 30 minutes
                
                # Log response
                logger.info(
                    f"Groq API response: model={model}, "
                    f"tokens={result.get('usage', {}).get('total_tokens', 'unknown')}, "
                    f"duration={duration:.3f}s"
                )
                
                return result
                
        except aiohttp.ClientError as e:
            error_msg = f"Groq API network error: {str(e)}"
            logger.error(error_msg)
            raise GroqAPIError(error_msg)
        except Exception as e:
            error_msg = f"Groq API unexpected error: {str(e)}"
            logger.error(error_msg)
            raise GroqAPIError(error_msg)
    
    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        project_id: Optional[str] = None,
        use_cache: bool = True,
        use_aggressive_fallback: bool = False
    ) -> Dict:
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
            API response dict
            
        Validates: Requirements 17.1, 17.2, 17.4
        """
        try:
            # Try primary model first
            logger.info(f"Attempting Groq API call with primary model: {self.primary_model}")
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
        except GroqAPIError as e:
            error_str = str(e)
            
            # Check if it's a rate limit error and aggressive fallback is enabled
            is_rate_limit = "rate limit" in error_str.lower() or "429" in error_str
            
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
    
    def _track_token_usage(self, project_id: str, usage: Dict):
        """
        Track token usage per project
        
        Args:
            project_id: Project ID
            usage: Usage dict from API response
            
        Validates: Requirements 17.3
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
    
    def get_token_usage(self, project_id: str) -> Dict:
        """
        Get token usage statistics for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with token usage statistics
            
        Validates: Requirements 17.3
        """
        return self._token_usage.get(project_id, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "requests": 0
        })
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Groq API client session closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
