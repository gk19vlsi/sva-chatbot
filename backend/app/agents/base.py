"""
Agent base class for multi-agent pipeline

This module defines the abstract base class for all agents in the SVA-Chatbot system.
Each agent performs a specific task in the processing pipeline.

Implements Requirements 16.1, 16.3, 19.5
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from pydantic import BaseModel

from app.clients.base import LLMClient, LLMAPIError
from app.utils.structured_logging import log_agent_execution, log_error
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineContext(BaseModel):
    """Context passed between agents in the pipeline"""
    project_id: str
    data: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


class AgentResult(BaseModel):
    """Result returned by an agent execution"""
    agent_name: str
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        arbitrary_types_allowed = True


class Agent(ABC):
    """
    Abstract base class for all agents in the pipeline
    
    Each agent must implement the execute() method to perform its specific task.
    The base class provides common functionality like LLM API calls with retry logic.
    
    Validates: Requirements 16.1, 16.3
    """
    
    def __init__(self, name: str, llm_client: LLMClient, db: AsyncIOMotorDatabase):
        """
        Initialize agent
        
        Args:
            name: Agent name for logging and identification
            llm_client: LLM API client for LLM interactions (provider-agnostic)
            db: MongoDB database instance
        """
        self.name = name
        self.llm_client = llm_client
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute agent-specific logic
        
        This method must be implemented by each concrete agent class.
        
        Args:
            context: Pipeline context containing project_id and shared data
            
        Returns:
            AgentResult with execution results
            
        Validates: Requirements 16.1
        """
        pass
    
    async def call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        project_id: Optional[str] = None
    ) -> str:
        """
        Make LLM API call with automatic fallback and retry logic
        
        This method handles:
        - Primary model attempt with fallback to secondary model
        - Exponential backoff retry on failures
        - Token usage tracking
        - Error logging
        
        Args:
            system_prompt: System message defining agent role and instructions
            user_prompt: User message with the actual task
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            project_id: Project ID for token tracking
            
        Returns:
            Generated text response from LLM
            
        Raises:
            LLMAPIError: If all retry attempts fail
            
        Validates: Requirements 16.3, 17.1, 17.2
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        max_retries = 2  # Reduced from 3 to 2 for optimization
        base_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"LLM API call attempt {attempt + 1}/{max_retries} "
                    f"for agent {self.name}"
                )
                
                # Add small delay before API call to avoid rate limits
                if settings.enable_rate_limit_delays and attempt > 0:
                    delay = settings.api_call_delay_seconds
                    self.logger.info(f"Rate limit delay: {delay}s before retry")
                    await asyncio.sleep(delay)
                
                # Use fallback method which tries primary then fallback model
                response = await self.llm_client.chat_completion_with_fallback(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    project_id=project_id,
                    use_aggressive_fallback=settings.use_aggressive_fallback
                )
                
                # Extract content from response
                content = response["choices"][0]["message"]["content"]
                
                self.logger.info(
                    f"LLM API call succeeded for agent {self.name} "
                    f"(attempt {attempt + 1})"
                )
                
                return content
                
            except LLMAPIError as e:
                self.logger.warning(
                    f"LLM API call failed for agent {self.name} "
                    f"(attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                
                # If this was the last attempt, raise the error
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"All retry attempts exhausted for agent {self.name}"
                    )
                    raise
                
                # Exponential backoff before retry
                delay = base_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        # This should never be reached due to the raise in the loop
        raise LLMAPIError("Unexpected error in retry logic", provider="unknown")
    
    async def _log_execution(
        self,
        context: PipelineContext,
        result: AgentResult
    ):
        """
        Log agent execution for performance tracking with structured logging
        
        Args:
            context: Pipeline context
            result: Agent execution result
            
        Validates: Requirements 16.5, 19.5
        """
        try:
            # Log with structured logging
            log_agent_execution(
                agent_name=self.name,
                project_id=context.project_id,
                status="success" if result.success else "failure",
                duration=result.execution_time or 0.0,
                error=result.error,
                data_keys=list(result.data.keys()) if result.data else []
            )
            
            # Store execution metrics in database
            await self.db.agent_executions.insert_one({
                "agent_name": self.name,
                "project_id": context.project_id,
                "success": result.success,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp,
                "error": result.error
            })
            
            self.logger.info(
                f"Agent {self.name} execution logged: "
                f"success={result.success}, time={result.execution_time}s"
            )
        except Exception as e:
            log_error(
                error_type="AgentLoggingError",
                error_message=f"Failed to log agent execution: {str(e)}",
                context={
                    "agent_name": self.name,
                    "project_id": context.project_id
                }
            )
