"""
SVA Generator Agent

This agent generates SystemVerilog Assertions from requirements and RTL analysis.
This is a simplified proof-of-concept version that generates assertions from
simple requirements without full pipeline integration.
Uses advanced prompt engineering with few-shot examples and structured output.
Uses enhanced traceability extraction for comprehensive tracking.

Implements Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.1, 8.2, 8.3
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId

from app.agents.base import Agent, AgentResult, PipelineContext
from app.agents.prompt_templates import SVAGeneratorPrompts
from app.clients.groq_client import GroqClient
from app.utils.traceability import build_assertion_traceability
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class SVAGeneratorAgent(Agent):
    """
    Simplified SVA Generator Agent for proof of concept
    
    Generates SystemVerilog Assertions from requirements with basic RTL context.
    This version focuses on core assertion generation without full alignment pipeline.
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    
    def __init__(self, groq_client: GroqClient, db: AsyncIOMotorDatabase):
        """
        Initialize SVA Generator Agent
        
        Args:
            groq_client: Groq API client for LLM interactions
            db: MongoDB database instance
        """
        super().__init__(name="SVAGenerator", groq_client=groq_client, db=db)
    
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute SVA generation for a project
        
        Args:
            context: Pipeline context with project_id
            
        Returns:
            AgentResult with generated assertions
            
        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting SVA generation for project {context.project_id}")
            
            # Load requirements from context or database
            requirements = await self._load_requirements(context)
            
            if not requirements:
                self.logger.warning(f"No requirements found for project {context.project_id}")
                return AgentResult(
                    agent_name=self.name,
                    success=True,
                    data={"assertions": []},
                    execution_time=self._calculate_execution_time(start_time)
                )
            
            # Load RTL context (simplified - just basic module info)
            rtl_context = await self._load_rtl_context(context)
            
            # Generate assertions for each requirement
            generated_assertions = []
            
            # Batch requirements by category for efficient processing
            from app.utils.batching import batch_requirements_by_similarity
            requirement_batches = batch_requirements_by_similarity(
                requirements,
                max_batch_size=3
            )
            
            logger.info(f"Processing {len(requirement_batches)} batches of requirements")
            
            for batch in requirement_batches:
                for req in batch:
                    try:
                        assertion = await self._generate_assertion(
                            requirement=req,
                            rtl_context=rtl_context,
                            project_id=context.project_id
                        )
                        
                        if assertion:
                            # Store assertion in database
                            assertion_id = await self._store_assertion(
                                project_id=context.project_id,
                                assertion=assertion
                            )
                            
                            assertion["id"] = str(assertion_id)
                            generated_assertions.append(assertion)
                            
                            self.logger.info(
                                f"Generated assertion {assertion_id} for requirement {req.get('requirement_id', 'unknown')}"
                            )
                    
                    except Exception as e:
                        self.logger.error(f"Failed to generate assertion for requirement: {e}")
                        continue
            
            execution_time = self._calculate_execution_time(start_time)
            
            result = AgentResult(
                agent_name=self.name,
                success=True,
                data={
                    "assertions": generated_assertions,
                    "count": len(generated_assertions)
                },
                execution_time=execution_time
            )
            
            await self._log_execution(context, result)
            
            self.logger.info(
                f"SVA generation completed: {len(generated_assertions)} assertions generated"
            )
            
            return result
            
        except Exception as e:
            execution_time = self._calculate_execution_time(start_time)
            error_msg = f"SVA generation failed: {str(e)}"
            self.logger.error(error_msg)
            
            result = AgentResult(
                agent_name=self.name,
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
            
            await self._log_execution(context, result)
            
            return result
    
    async def _load_requirements(self, context: PipelineContext) -> List[Dict]:
        """
        Load requirements from context or database
        
        Args:
            context: Pipeline context
            
        Returns:
            List of requirement dictionaries
        """
        # First check if requirements are in context
        if "requirements" in context.data:
            return context.data["requirements"]
        
        # Otherwise load from database
        try:
            specs = await self.db.specifications.find(
                {"project_id": ObjectId(context.project_id)}
            ).to_list(length=None)
            
            requirements = []
            for spec in specs:
                if "parsed_requirements" in spec:
                    requirements.extend(spec["parsed_requirements"])
            
            return requirements
            
        except Exception as e:
            self.logger.error(f"Failed to load requirements: {e}")
            return []
    
    async def _load_rtl_context(self, context: PipelineContext) -> Dict:
        """
        Load RTL context from database
        
        Args:
            context: Pipeline context
            
        Returns:
            Dictionary with RTL context (modules, signals, clocks, resets)
        """
        # Check if RTL context is in pipeline context
        if "rtl_context" in context.data:
            return context.data["rtl_context"]
        
        # Otherwise load from database
        try:
            rtl_designs = await self.db.rtl_designs.find(
                {"project_id": ObjectId(context.project_id)}
            ).to_list(length=None)
            
            if not rtl_designs:
                # Return default context if no RTL found
                return {
                    "modules": [],
                    "default_clock": "clk",
                    "default_reset": "rst_n"
                }
            
            # Extract basic context from first RTL design
            rtl = rtl_designs[0]
            analysis = rtl.get("analysis", {})
            modules = analysis.get("modules", [])
            
            # Get default clock and reset from first module
            default_clock = "clk"
            default_reset = "rst_n"
            
            if modules:
                first_module = modules[0]
                clocks = first_module.get("clocks", [])
                resets = first_module.get("resets", [])
                
                if clocks:
                    default_clock = clocks[0]
                if resets:
                    default_reset = resets[0]
            
            return {
                "modules": modules,
                "default_clock": default_clock,
                "default_reset": default_reset
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load RTL context: {e}")
            return {
                "modules": [],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
    
    async def _generate_assertion(
        self,
        requirement: Dict,
        rtl_context: Dict,
        project_id: str
    ) -> Optional[Dict]:
        """
        Generate a single SVA assertion from a requirement
        
        Args:
            requirement: Requirement dictionary
            rtl_context: RTL context with modules and signals
            project_id: Project ID for token tracking
            
        Returns:
            Dictionary with assertion details or None if generation fails
            
        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
        """
        # Extract requirement details
        req_text = requirement.get("text", "")
        req_id = requirement.get("requirement_id", "unknown")
        category = requirement.get("category", "functional")
        temporal_keywords = requirement.get("temporal_keywords", [])
        entities = requirement.get("entities", [])
        
        # Determine assertion type based on temporal keywords
        has_temporal = len(temporal_keywords) > 0
        assertion_type = "concurrent" if has_temporal else "immediate"
        
        # Build system prompt
        system_prompt = self._build_system_prompt()
        
        # Build user prompt with requirement and context
        user_prompt = self._build_user_prompt(
            requirement_text=req_text,
            requirement_id=req_id,
            category=category,
            temporal_keywords=temporal_keywords,
            entities=entities,
            rtl_context=rtl_context,
            assertion_type=assertion_type
        )
        
        try:
            # Call LLM to generate assertion
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,  # Low temperature for more deterministic output
                max_tokens=1024,
                project_id=project_id
            )
            
            # Parse response (expecting JSON format)
            assertion_data = self._parse_llm_response(response)
            
            if not assertion_data:
                self.logger.warning(f"Failed to parse LLM response for requirement {req_id}")
                return None
            
            # Build complete assertion record with enhanced traceability
            rtl_module_name = assertion_data.get("module", rtl_context.get("modules", [{}])[0].get("name", "unknown") if rtl_context.get("modules") else "unknown")
            signals = assertion_data.get("signals", entities)
            
            # Build enhanced traceability with line numbers
            traceability = await self._build_enhanced_traceability(
                requirement_id=req_id,
                requirement_text=req_text,
                assertion_code=assertion_data.get("code", ""),
                rtl_module=rtl_module_name,
                signals=signals,
                project_id=project_id
            )
            
            assertion = {
                "requirement_id": req_id,
                "assertion_code": assertion_data.get("code", ""),
                "assertion_type": assertion_type,
                "category": category,
                "rtl_module": rtl_module_name,
                "confidence_score": assertion_data.get("confidence", 0.8),
                "explanation": assertion_data.get("explanation", ""),
                "traceability": traceability
            }
            
            return assertion
            
        except Exception as e:
            self.logger.error(f"Failed to generate assertion for requirement {req_id}: {e}")
            return None
    
    async def _build_enhanced_traceability(
        self,
        requirement_id: str,
        requirement_text: str,
        assertion_code: str,
        rtl_module: str,
        signals: List[str],
        project_id: str
    ) -> Dict[str, Any]:
        """
        Build enhanced traceability with RTL line numbers
        
        Args:
            requirement_id: Requirement identifier
            requirement_text: Requirement text
            assertion_code: Generated assertion code
            rtl_module: RTL module name
            signals: List of signal names
            project_id: Project ID
            
        Returns:
            Enhanced traceability dictionary
            
        Validates: Requirements 8.1, 8.2, 8.3
        """
        try:
            # Try to load RTL code from database
            rtl_designs = await self.db.rtl_designs.find(
                {"project_id": ObjectId(project_id)}
            ).to_list(length=None)
            
            line_numbers = []
            
            if rtl_designs and signals:
                # Get RTL source code
                for rtl in rtl_designs:
                    rtl_code = rtl.get("source_code", "")
                    if rtl_code:
                        # Use traceability extractor to get line numbers
                        from app.utils.traceability import extract_signal_line_numbers
                        
                        signal_lines = extract_signal_line_numbers(
                            rtl_code, signals, rtl_module
                        )
                        
                        # Collect all line numbers
                        for sig_lines in signal_lines.values():
                            line_numbers.extend(sig_lines)
                        
                        # Remove duplicates and sort
                        line_numbers = sorted(list(set(line_numbers)))
                        
                        if line_numbers:
                            break  # Found line numbers, stop searching
            
            # Build traceability record
            traceability = {
                "spec_reference": requirement_id,
                "requirement_text": requirement_text,
                "rtl_signals": signals,
                "rtl_module": rtl_module,
                "line_numbers": line_numbers
            }
            
            return traceability
            
        except Exception as e:
            self.logger.error(f"Error building enhanced traceability: {e}")
            # Return basic traceability on error
            return {
                "spec_reference": requirement_id,
                "requirement_text": requirement_text,
                "rtl_signals": signals,
                "rtl_module": rtl_module,
                "line_numbers": []
            }
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt for SVA generation using advanced template
        
        Returns:
            System prompt string
        """
        return SVAGeneratorPrompts.get_system_prompt()
    
    def _build_user_prompt(
        self,
        requirement_text: str,
        requirement_id: str,
        category: str,
        temporal_keywords: List[str],
        entities: List[str],
        rtl_context: Dict,
        assertion_type: str
    ) -> str:
        """
        Build user prompt with requirement and context using advanced template
        
        Args:
            requirement_text: The requirement text
            requirement_id: Requirement identifier
            category: Requirement category
            temporal_keywords: List of temporal keywords found
            entities: List of entity names (signals, modules, etc.)
            rtl_context: RTL context dictionary
            assertion_type: Type of assertion to generate
            
        Returns:
            User prompt string
        """
        return SVAGeneratorPrompts.get_generation_prompt(
            req_text=requirement_text,
            req_id=requirement_id,
            category=category,
            temporal_keywords=temporal_keywords,
            entities=entities,
            rtl_context=rtl_context,
            assertion_type=assertion_type
        )
    
    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """
        Parse LLM response to extract assertion data
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed assertion dictionary or None if parsing fails
        """
        try:
            # Try to parse as JSON
            # First, try to find JSON in the response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            data = json.loads(response)
            
            # Validate required fields
            if "code" not in data:
                self.logger.warning("LLM response missing 'code' field")
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            self.logger.debug(f"Response was: {response}")
            return None
    
    async def _store_assertion(
        self,
        project_id: str,
        assertion: Dict
    ) -> ObjectId:
        """
        Store generated assertion in database
        
        Args:
            project_id: Project ID
            assertion: Assertion dictionary
            
        Returns:
            Inserted assertion ObjectId
            
        Validates: Requirements 18.3
        """
        # Prepare assertion document for database
        assertion_doc = {
            "project_id": ObjectId(project_id),
            "requirement_id": assertion["requirement_id"],
            "assertion_code": assertion["assertion_code"],
            "assertion_type": assertion["assertion_type"],
            "category": assertion["category"],
            "rtl_module": assertion["rtl_module"],
            "confidence_score": assertion["confidence_score"],
            "explanation": assertion["explanation"],
            "traceability": assertion["traceability"],
            "validation": None,  # Will be filled by validation agent
            "user_feedback": {
                "rating": None,
                "modified": False,
                "comments": None,
                "feedback_at": None
            },
            "generated_at": datetime.utcnow(),
            "agent_version": "1.0.0-poc"
        }
        
        result = await self.db.assertions.insert_one(assertion_doc)
        
        self.logger.info(f"Stored assertion {result.inserted_id} in database")
        
        return result.inserted_id
    
    def _calculate_execution_time(self, start_time: datetime) -> float:
        """
        Calculate execution time in seconds
        
        Args:
            start_time: Execution start time
            
        Returns:
            Execution time in seconds
        """
        return (datetime.utcnow() - start_time).total_seconds()
