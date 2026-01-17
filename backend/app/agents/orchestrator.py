"""
Orchestrator for Multi-Agent Pipeline

Manages the lifecycle and execution of all five agents in the SVA-Chatbot pipeline.
Implements sequential execution, context passing, retry logic, and performance tracking.
Integrates with WebSocket for real-time status updates.

Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5, 9.1, 9.2, 9.3, 9.4, 9.5
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

from app.agents.base import Agent, PipelineContext, AgentResult
from app.agents.spec_parser import SpecificationParserAgent
from app.agents.rtl_analyzer import RTLAnalyzerAgent
from app.agents.alignment import AlignmentAgent
from app.agents.sva_generator import SVAGeneratorAgent
from app.agents.validation import ValidationAgent
from app.clients.groq_client import GroqClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result of complete pipeline execution"""
    
    def __init__(self):
        self.success: bool = False
        self.agent_results: List[AgentResult] = []
        self.final_data: Dict[str, Any] = {}
        self.total_execution_time: float = 0.0
        self.error: Optional[str] = None
        self.timestamp: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "agent_results": [
                {
                    "agent_name": r.agent_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error": r.error,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None
                }
                for r in self.agent_results
            ],
            "final_data": self.final_data,
            "total_execution_time": self.total_execution_time,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class Orchestrator:
    """
    Orchestrator for the five-agent SVA generation pipeline
    
    Responsibilities:
    - Initialize all five agents
    - Execute agents in correct sequence
    - Pass context between agents
    - Handle agent failures with retry logic
    - Track performance metrics
    
    Pipeline sequence:
    1. Specification Parser - Extract requirements from documents
    2. RTL Analyzer - Parse and analyze SystemVerilog code
    3. Alignment Agent - Map requirements to RTL elements
    4. SVA Generator - Generate assertions from alignments
    5. Validation Agent - Validate and score assertions
    
    Validates: Requirements 16.1, 16.2, 16.3, 16.4, 16.5
    """
    
    def __init__(self, groq_client: GroqClient, db: AsyncIOMotorDatabase):
        """
        Initialize orchestrator and all agents
        
        Args:
            groq_client: Groq API client for LLM interactions
            db: MongoDB database instance
            
        Validates: Requirement 16.1
        """
        self.groq_client = groq_client
        self.db = db
        
        # Initialize all five agents in sequence
        self.agents: Dict[str, Agent] = {
            "spec_parser": SpecificationParserAgent(groq_client, db),
            "rtl_analyzer": RTLAnalyzerAgent(groq_client, db),
            "alignment": AlignmentAgent(groq_client, db),
            "sva_generator": SVAGeneratorAgent(groq_client, db),
            "validation": ValidationAgent(groq_client, db)
        }
        
        # Define pipeline execution order
        self.pipeline_sequence = [
            "spec_parser",
            "rtl_analyzer",
            "alignment",
            "sva_generator",
            "validation"
        ]
        
        logger.info("Orchestrator initialized with 5 agents")
    
    async def execute_pipeline(
        self,
        project_id: str,
        initial_data: Optional[Dict[str, Any]] = None,
        websocket_manager: Optional[Any] = None
    ) -> PipelineResult:
        """
        Execute the complete five-agent pipeline
        
        Args:
            project_id: Project ID for context
            initial_data: Optional initial data to pass to first agent
            websocket_manager: Optional WebSocket connection manager for real-time updates
            
        Returns:
            PipelineResult with execution results
            
        Validates: Requirements 16.1, 16.2, 16.4, 9.1, 9.2
        """
        start_time = datetime.utcnow()
        result = PipelineResult()
        
        try:
            logger.info(f"Starting pipeline execution for project {project_id}")
            
            # Send pipeline start notification
            if websocket_manager:
                await websocket_manager.send_status_update(
                    project_id=project_id,
                    agent_name="pipeline",
                    status="started",
                    data={"message": "Pipeline execution started"}
                )
            
            # Initialize context
            context = PipelineContext(
                project_id=project_id,
                data=initial_data or {}
            )
            
            # Execute agents in sequence
            for agent_name in self.pipeline_sequence:
                agent = self.agents[agent_name]
                
                logger.info(f"Executing agent: {agent_name}")
                
                # Send agent start notification
                if websocket_manager:
                    await websocket_manager.send_status_update(
                        project_id=project_id,
                        agent_name=agent_name,
                        status="started"
                    )
                
                # Execute agent with retry logic
                agent_result = await self._execute_agent_with_retry(
                    agent=agent,
                    context=context,
                    websocket_manager=websocket_manager,
                    project_id=project_id
                )
                
                # Store agent result
                result.agent_results.append(agent_result)
                
                # Check if agent succeeded
                if not agent_result.success:
                    error_msg = f"Agent {agent_name} failed: {agent_result.error}"
                    logger.error(error_msg)
                    result.success = False
                    result.error = error_msg
                    
                    # Send error notification
                    if websocket_manager:
                        await websocket_manager.send_error(
                            project_id=project_id,
                            error=error_msg,
                            agent_name=agent_name
                        )
                    
                    break
                
                # Pass agent results to next agent via context
                context.data.update(agent_result.data)
                
                # Add delay between agents to avoid rate limits (Groq free tier)
                if settings.enable_rate_limit_delays and agent_name != self.pipeline_sequence[-1]:
                    delay = settings.agent_delay_seconds
                    logger.info(f"Waiting {delay}s before next agent (rate limit management)")
                    await asyncio.sleep(delay)
                
                # Send agent completion notification
                if websocket_manager:
                    await websocket_manager.send_status_update(
                        project_id=project_id,
                        agent_name=agent_name,
                        status="completed",
                        data={
                            "execution_time": agent_result.execution_time,
                            "summary": self._get_agent_summary(agent_name, agent_result)
                        }
                    )
                
                # Stream assertions if this is the SVA Generator
                if agent_name == "sva_generator" and websocket_manager:
                    assertions = agent_result.data.get("assertions", [])
                    for assertion in assertions:
                        await websocket_manager.send_assertion(
                            project_id=project_id,
                            assertion=assertion
                        )
                
                logger.info(
                    f"Agent {agent_name} completed successfully "
                    f"in {agent_result.execution_time:.2f}s"
                )
            
            # If all agents succeeded
            if len(result.agent_results) == len(self.pipeline_sequence):
                if all(r.success for r in result.agent_results):
                    result.success = True
                    result.final_data = context.data
                    logger.info("Pipeline execution completed successfully")
                    
                    # Send completion notification
                    if websocket_manager:
                        await websocket_manager.send_completion(
                            project_id=project_id,
                            result=result.to_dict()
                        )
            
            # Calculate total execution time
            end_time = datetime.utcnow()
            result.total_execution_time = (end_time - start_time).total_seconds()
            
            # Track pipeline metrics
            await self._track_pipeline_metrics(project_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed with exception: {str(e)}")
            result.success = False
            result.error = str(e)
            
            # Send error notification
            if websocket_manager:
                await websocket_manager.send_error(
                    project_id=project_id,
                    error=str(e)
                )
            
            end_time = datetime.utcnow()
            result.total_execution_time = (end_time - start_time).total_seconds()
            
            return result
    
    async def _execute_agent_with_retry(
        self,
        agent: Agent,
        context: PipelineContext,
        max_retries: int = 2,  # Reduced from 3 to 2 for optimization
        websocket_manager: Optional[Any] = None,
        project_id: Optional[str] = None
    ) -> AgentResult:
        """
        Execute an agent with exponential backoff retry logic
        
        Args:
            agent: Agent to execute
            context: Pipeline context
            max_retries: Maximum number of retry attempts
            
        Returns:
            AgentResult from successful execution or final failure
            
        Validates: Requirement 16.3
        """
        base_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Executing agent {agent.name} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                
                # Execute agent
                agent_start = datetime.utcnow()
                result = await agent.execute(context)
                agent_end = datetime.utcnow()
                
                # Set execution time if not already set
                if result.execution_time is None:
                    result.execution_time = (agent_end - agent_start).total_seconds()
                
                # If successful, return immediately
                if result.success:
                    logger.info(f"Agent {agent.name} succeeded on attempt {attempt + 1}")
                    return result
                
                # If failed but not last attempt, retry
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Agent {agent.name} failed on attempt {attempt + 1}, "
                        f"retrying in {delay}s: {result.error}"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed
                    logger.error(
                        f"Agent {agent.name} failed after {max_retries} attempts: "
                        f"{result.error}"
                    )
                    return result
                    
            except Exception as e:
                logger.error(
                    f"Agent {agent.name} raised exception on attempt {attempt + 1}: "
                    f"{str(e)}"
                )
                
                # If last attempt, return failure result
                if attempt == max_retries - 1:
                    return AgentResult(
                        agent_name=agent.name,
                        success=False,
                        error=str(e),
                        execution_time=0.0
                    )
                
                # Exponential backoff before retry
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # Should never reach here
        return AgentResult(
            agent_name=agent.name,
            success=False,
            error="Unexpected error in retry logic",
            execution_time=0.0
        )
    
    async def _track_pipeline_metrics(
        self,
        project_id: str,
        result: PipelineResult
    ):
        """
        Track pipeline execution metrics in database
        
        Args:
            project_id: Project ID
            result: Pipeline execution result
            
        Validates: Requirement 16.5
        """
        try:
            # Store pipeline execution record
            await self.db.pipeline_executions.insert_one({
                "project_id": project_id,
                "success": result.success,
                "total_execution_time": result.total_execution_time,
                "agent_count": len(result.agent_results),
                "timestamp": result.timestamp,
                "error": result.error,
                "agent_metrics": [
                    {
                        "agent_name": r.agent_name,
                        "success": r.success,
                        "execution_time": r.execution_time,
                        "error": r.error
                    }
                    for r in result.agent_results
                ]
            })
            
            logger.info(
                f"Pipeline metrics tracked for project {project_id}: "
                f"success={result.success}, time={result.total_execution_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to track pipeline metrics: {str(e)}")
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get status information for a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent status dictionary
        """
        if agent_name not in self.agents:
            return {
                "error": f"Agent {agent_name} not found",
                "available_agents": list(self.agents.keys())
            }
        
        agent = self.agents[agent_name]
        
        return {
            "name": agent.name,
            "type": agent.__class__.__name__,
            "status": "ready"
        }
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get status of the entire pipeline
        
        Returns:
            Pipeline status dictionary
        """
        return {
            "agents": [
                {
                    "name": agent_name,
                    "type": self.agents[agent_name].__class__.__name__,
                    "position": idx + 1
                }
                for idx, agent_name in enumerate(self.pipeline_sequence)
            ],
            "total_agents": len(self.agents),
            "pipeline_sequence": self.pipeline_sequence
        }
    
    def _get_agent_summary(self, agent_name: str, result: AgentResult) -> Dict[str, Any]:
        """
        Generate a summary of agent execution results for WebSocket updates
        
        Args:
            agent_name: Name of the agent
            result: Agent execution result
            
        Returns:
            Summary dictionary
            
        Validates: Requirement 9.2
        """
        summary = {}
        
        if agent_name == "spec_parser":
            requirements = result.data.get("requirements", [])
            summary["requirements_count"] = len(requirements)
        
        elif agent_name == "rtl_analyzer":
            modules = result.data.get("modules", [])
            summary["modules_count"] = len(modules)
        
        elif agent_name == "alignment":
            alignments = result.data.get("alignments", [])
            summary["alignments_count"] = len(alignments)
            high_confidence = sum(1 for a in alignments if a.get("confidence_score", 0) >= 0.8)
            summary["high_confidence_count"] = high_confidence
        
        elif agent_name == "sva_generator":
            assertions = result.data.get("assertions", [])
            summary["assertions_count"] = len(assertions)
        
        elif agent_name == "validation":
            assertions = result.data.get("assertions", [])
            valid_count = sum(1 for a in assertions if a.get("syntax_valid", False))
            summary["valid_assertions"] = valid_count
            summary["total_assertions"] = len(assertions)
        
        return summary
