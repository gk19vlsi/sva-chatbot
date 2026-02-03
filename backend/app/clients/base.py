"""
Base client interface and exceptions for LLM providers

This module defines the common interface that all LLM clients must implement,
ensuring type safety and consistency across different providers (Groq, OpenAI, etc.).
"""
from typing import Protocol, List, Dict, Optional, Any
from typing_extensions import runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """
    Protocol defining the interface for LLM clients
    
    This protocol ensures that all LLM client implementations (GroqClient, OpenAIClient, etc.)
    provide a consistent interface for agents to interact with, enabling seamless provider
    switching without code changes.
    
    All implementing classes must provide:
    - Async chat completion methods with caching and fallback support
    - Token usage tracking per project
    - Proper session management and cleanup
    
    Validates: Requirements 1.1, 4.4
    """
    
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
        Make a chat completion request to the LLM provider
        
        This method sends a chat completion request to the underlying LLM API
        (Groq, OpenAI, etc.) and returns the response in a standardized format.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Example: [{"role": "user", "content": "Hello"}]
            model: Specific model to use. If None, uses the client's primary model.
            temperature: Sampling temperature (0.0 to 2.0). Lower values make output
                        more focused and deterministic, higher values more random.
            max_tokens: Maximum number of tokens to generate in the response.
            top_p: Nucleus sampling parameter (0.0 to 1.0). Alternative to temperature
                  for controlling randomness.
            project_id: Optional project identifier for tracking token usage per project.
            use_fallback: If True, uses the fallback model instead of primary model.
            use_cache: If True, checks cache for previous identical requests and caches
                      successful responses to reduce API calls and costs.
        
        Returns:
            Dict containing the API response with standardized structure:
            {
                "id": str,              # Response ID
                "model": str,           # Model used
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
        
        Raises:
            LLMAPIError: If the API call fails due to authentication, network,
                        rate limiting, or other errors.
        
        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
        """
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
        """
        Make a chat completion request with automatic fallback to secondary model
        
        This method attempts to use the primary model first, and automatically falls
        back to the secondary model if the primary fails. This provides resilience
        against model unavailability, rate limits, and other transient errors.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Example: [{"role": "user", "content": "Hello"}]
            temperature: Sampling temperature (0.0 to 2.0). Lower values make output
                        more focused and deterministic, higher values more random.
            max_tokens: Maximum number of tokens to generate in the response.
            top_p: Nucleus sampling parameter (0.0 to 1.0). Alternative to temperature
                  for controlling randomness.
            project_id: Optional project identifier for tracking token usage per project.
            use_cache: If True, checks cache for previous identical requests and caches
                      successful responses to reduce API calls and costs.
            use_aggressive_fallback: If True, immediately uses fallback model on rate
                                    limit errors without retrying primary model.
        
        Returns:
            Dict containing the API response with standardized structure (same as
            chat_completion method).
        
        Raises:
            LLMAPIError: If both primary and fallback models fail.
        
        Validates: Requirements 2.1, 2.2, 2.3, 2.4
        """
        ...
    
    def get_token_usage(self, project_id: str) -> Dict[str, int]:
        """
        Get token usage statistics for a specific project
        
        Returns accumulated token usage across all API calls made for the given
        project. This enables cost tracking and monitoring per project.
        
        Args:
            project_id: Project identifier to get usage statistics for.
        
        Returns:
            Dict containing token usage statistics:
            {
                "prompt_tokens": int,      # Total tokens in prompts
                "completion_tokens": int,  # Total tokens in completions
                "total_tokens": int,       # Sum of prompt and completion tokens
                "requests": int            # Number of API requests made
            }
            
            Returns zeros for all fields if project_id has no recorded usage.
        
        Validates: Requirements 1.5, 10.1, 10.2, 10.3
        """
        ...
    
    async def close(self) -> None:
        """
        Close the client session and cleanup resources
        
        This method should be called when the client is no longer needed to properly
        release network connections, close HTTP sessions, and cleanup any other
        resources held by the client.
        
        Should be idempotent - calling multiple times should be safe.
        
        Typically used with async context managers:
            async with client:
                # Use client
                pass
            # close() called automatically
        
        Validates: Requirements 1.8
        """
        ...


class LLMAPIError(Exception):
    """
    Exception raised for LLM API errors
    
    This exception provides a consistent error interface across different LLM providers,
    including provider identification and optional HTTP status codes for debugging.
    
    Attributes:
        message: Human-readable error description
        provider: Name of the LLM provider (e.g., "groq", "openai")
        status_code: Optional HTTP status code from the API response
        original_error: Optional original exception that caused this error
    
    Validates: Requirements 1.4, 9.1, 9.2
    """
    
    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize LLM API error
        
        Args:
            message: Human-readable error description
            provider: Name of the LLM provider (e.g., "groq", "openai")
            status_code: Optional HTTP status code from the API response
            original_error: Optional original exception that caused this error
        """
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.original_error = original_error
        
        # Format error message with provider prefix
        formatted_message = f"[{provider}] {message}"
        super().__init__(formatted_message)
