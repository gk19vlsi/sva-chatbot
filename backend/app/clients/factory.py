"""
LLM Client Factory

This module provides a factory pattern for creating LLM clients based on configuration.
The factory abstracts away provider-specific instantiation logic, allowing agents to
receive the appropriate client (Groq, OpenAI, etc.) without knowing which provider
is being used.

This enables:
- Easy provider switching through configuration
- Dependency injection for agents
- Centralized validation of provider configuration
- Type-safe client creation

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 3.5
"""
from typing import Union
from ..config import settings
from .groq_client import GroqClient
from .openai_client import OpenAIClient


class LLMClientFactory:
    """
    Factory for creating LLM clients based on configuration
    
    This factory creates and returns the appropriate LLM client (GroqClient or
    OpenAIClient) based on the LLM_PROVIDER setting in the application configuration.
    It validates that the selected provider has the required API key configured and
    raises clear errors for invalid configurations.
    
    Usage:
        # In agent initialization
        client = LLMClientFactory.create_client()
        
        # Check which provider is configured
        provider_name = LLMClientFactory.get_provider_name()
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """
    
    @staticmethod
    def create_client() -> Union[GroqClient, OpenAIClient]:
        """
        Create and return the configured LLM client
        
        This method reads the LLM_PROVIDER setting from configuration and creates
        the appropriate client instance. It validates that:
        1. The provider name is valid ("groq" or "openai")
        2. The required API key for the selected provider is configured
        
        Returns:
            GroqClient if settings.llm_provider is "groq"
            OpenAIClient if settings.llm_provider is "openai"
        
        Raises:
            ValueError: If the provider is invalid or required configuration is missing.
                       Error messages clearly indicate what needs to be fixed:
                       - "Invalid LLM provider: {provider}. Must be 'groq' or 'openai'"
                       - "GROQ_API_KEY is required when using Groq provider"
                       - "OPENAI_API_KEY is required when using OpenAI provider"
        
        Examples:
            >>> # With LLM_PROVIDER=groq and GROQ_API_KEY set
            >>> client = LLMClientFactory.create_client()
            >>> isinstance(client, GroqClient)
            True
            
            >>> # With LLM_PROVIDER=openai and OPENAI_API_KEY set
            >>> client = LLMClientFactory.create_client()
            >>> isinstance(client, OpenAIClient)
            True
            
            >>> # With LLM_PROVIDER=invalid
            >>> client = LLMClientFactory.create_client()
            ValueError: Invalid LLM provider: invalid. Must be 'groq' or 'openai'
        
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 3.5
        """
        # Normalize provider name to lowercase for case-insensitive comparison
        provider = settings.llm_provider.lower()
        
        if provider == "groq":
            # Validate Groq API key is configured
            if not settings.groq_api_key:
                raise ValueError(
                    "GROQ_API_KEY is required when using Groq provider. "
                    "Please set GROQ_API_KEY in your .env file."
                )
            return GroqClient(api_key=settings.groq_api_key)
        
        elif provider == "openai":
            # Validate OpenAI API key is configured
            if not settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY is required when using OpenAI provider. "
                    "Please set OPENAI_API_KEY in your .env file."
                )
            return OpenAIClient(api_key=settings.openai_api_key)
        
        else:
            # Invalid provider name
            raise ValueError(
                f"Invalid LLM provider: {provider}. "
                f"Must be 'groq' or 'openai'. "
                f"Please set LLM_PROVIDER in your .env file to either 'groq' or 'openai'."
            )
    
    @staticmethod
    def get_provider_name() -> str:
        """
        Get the name of the configured LLM provider
        
        Returns the current LLM provider name from settings. This is useful for
        logging, metrics, and debugging to identify which provider is being used.
        
        Returns:
            str: The configured provider name (e.g., "groq", "openai")
        
        Examples:
            >>> # With LLM_PROVIDER=groq
            >>> LLMClientFactory.get_provider_name()
            'groq'
            
            >>> # With LLM_PROVIDER=openai
            >>> LLMClientFactory.get_provider_name()
            'openai'
        
        Validates: Requirements 4.4
        """
        return settings.llm_provider
