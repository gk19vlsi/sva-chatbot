"""
Application configuration management
"""
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
    groq_fallback_model: str = "llama-3.1-8b-instant"  # Updated to a supported model
    
    # OpenAI API Configuration
    openai_api_key: str = ""
    openai_primary_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"
    
    # JWT Configuration
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # Application Configuration
    environment: str = "development"
    debug: bool = True
    
    # File Upload Configuration
    max_file_size_mb: int = 50
    upload_dir: str = "./uploads"
    
    # Rate Limiting Configuration (for Groq free tier)
    enable_rate_limit_delays: bool = True  # Enable delays between API calls
    agent_delay_seconds: float = 2.0  # Delay between agent executions
    api_call_delay_seconds: float = 0.5  # Delay between individual API calls
    use_aggressive_fallback: bool = True  # Use fallback model more aggressively
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env without validation errors


settings = Settings()
