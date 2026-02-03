"""
Validation Agent

Validates generated SystemVerilog assertions for syntax correctness and quality.
Uses syntax checking and LLM-based quality analysis.
Uses advanced prompt engineering with detailed quality assessment.
"""
from typing import List, Dict, Any
from app.agents.base import Agent, PipelineContext, AgentResult
from app.agents.prompt_templates import ValidationPrompts
from app.clients.base import LLMClient
from app.utils.sva_validator import validate_sva_syntax
from bson import ObjectId
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ValidationAgent(Agent):
    """
    Agent responsible for validating generated assertions.
    
    Capabilities:
    - Validate SVA syntax
    - Detect vacuity (assertions that are always true/false)
    - Detect over-constraints (assertions that are too restrictive)
    - Calculate quality scores
    - Update assertion metadata with validation results
    """
    
    def __init__(self, llm_client: LLMClient, db):
        super().__init__("Validation", llm_client, db)
    
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute assertion validation.
        
        Args:
            context: Pipeline context containing generated assertions
            
        Returns:
            AgentResult with validation results
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract assertions from context
            assertions = context.data.get("assertions", [])
            
            if not assertions:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No assertions provided in context"
                )
            
            logger.info(f"Validating {len(assertions)} assertions")
            
            # Validate each assertion
            validated_assertions = []
            for assertion in assertions:
                validated = await self._validate_assertion(assertion)
                validated_assertions.append(validated)
            
            # Update assertions in database
            project_id = context.project_id
            if project_id:
                await self._update_assertions(validated_assertions)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate statistics
            valid_count = sum(1 for a in validated_assertions if a.get("syntax_valid", False))
            high_quality = sum(1 for a in validated_assertions if a.get("quality_score", 0) >= 0.8)
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "assertions": validated_assertions,
                    "execution_time": execution_time
                },
                metadata={
                    "total_assertions": len(validated_assertions),
                    "valid_syntax": valid_count,
                    "high_quality": high_quality
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Validation agent: {str(e)}")
            return AgentResult(
                success=False,
                agent_name=self.name,
                data={},
                error=str(e)
            )
    
    async def _validate_assertion(self, assertion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single assertion.
        
        Args:
            assertion: Assertion dictionary
            
        Returns:
            Enhanced assertion with validation results
        """
        assertion_code = assertion.get("assertion_code", "")
        assertion_id = assertion.get("id", "")
        requirement_text = assertion.get("traceability", {}).get("requirement_text", "")
        rtl_module = assertion.get("rtl_module", "")
        
        # Step 1: Syntax validation
        syntax_valid, syntax_error = validate_sva_syntax(assertion_code)
        
        # Step 2: Quality analysis using LLM with advanced prompts
        quality_analysis = await self._analyze_quality(
            assertion_code, requirement_text, rtl_module
        )
        
        # Step 3: Calculate quality score
        quality_score = self._calculate_quality_score(
            syntax_valid=syntax_valid,
            has_vacuity=quality_analysis.get("has_vacuity", False),
            has_over_constraint=quality_analysis.get("has_over_constraint", False),
            complexity=quality_analysis.get("complexity", "medium")
        )
        
        # Return enhanced assertion
        return {
            **assertion,
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error if not syntax_valid else None,
            "quality_score": quality_score,
            "vacuity_detected": quality_analysis.get("has_vacuity", False),
            "over_constraint_detected": quality_analysis.get("has_over_constraint", False),
            "quality_notes": quality_analysis.get("notes", ""),
            "validated_at": datetime.utcnow()
        }
    
    async def _analyze_quality(self, assertion_code: str, requirement_text: str = "",
                              rtl_module: str = "") -> Dict[str, Any]:
        """
        Analyze assertion quality using LLM with advanced prompts.
        
        Args:
            assertion_code: SVA assertion code
            requirement_text: Original requirement text
            rtl_module: Target RTL module
            
        Returns:
            Quality analysis dictionary
        """
        # Use advanced prompt template with detailed analysis
        system_prompt = ValidationPrompts.get_system_prompt()
        user_prompt = ValidationPrompts.get_quality_analysis_prompt(
            assertion_code, requirement_text, rtl_module
        )
        
        try:
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing assertion quality: {str(e)}")
            # Fallback: basic heuristics
            return {
                "has_vacuity": False,
                "vacuity_reason": "",
                "has_over_constraint": False,
                "over_constraint_reason": "",
                "complexity": "medium",
                "quality_score": 0.7,
                "notes": "Quality analysis unavailable due to LLM error"
            }
    
    def _calculate_quality_score(self, syntax_valid: bool, has_vacuity: bool,
                                 has_over_constraint: bool, complexity: str) -> float:
        """
        Calculate quality score for an assertion.
        
        Args:
            syntax_valid: Whether syntax is valid
            has_vacuity: Whether vacuity detected
            has_over_constraint: Whether over-constraint detected
            complexity: Complexity level
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        score = 1.0
        
        # Syntax validity is critical
        if not syntax_valid:
            score -= 0.5
        
        # Vacuity is a major issue
        if has_vacuity:
            score -= 0.3
        
        # Over-constraint is a moderate issue
        if has_over_constraint:
            score -= 0.2
        
        # Complexity affects score slightly
        complexity_penalties = {
            "simple": 0.0,
            "medium": 0.05,
            "complex": 0.1
        }
        score -= complexity_penalties.get(complexity, 0.05)
        
        return max(0.0, min(1.0, score))
    
    async def _update_assertions(self, assertions: List[Dict[str, Any]]):
        """
        Update assertions in database with validation results.
        
        Args:
            assertions: List of validated assertions
        """
        try:
            for assertion in assertions:
                assertion_id = assertion.get("id")
                if not assertion_id:
                    continue
                
                # Update assertion document
                await self.db.assertions.update_one(
                    {"_id": ObjectId(assertion_id)},
                    {
                        "$set": {
                            "syntax_valid": assertion.get("syntax_valid", False),
                            "syntax_error": assertion.get("syntax_error"),
                            "quality_score": assertion.get("quality_score", 0),
                            "vacuity_detected": assertion.get("vacuity_detected", False),
                            "over_constraint_detected": assertion.get("over_constraint_detected", False),
                            "quality_notes": assertion.get("quality_notes", ""),
                            "validated_at": assertion.get("validated_at")
                        }
                    }
                )
            
            logger.info(f"Updated {len(assertions)} assertions with validation results")
            
        except Exception as e:
            logger.error(f"Error updating assertions: {str(e)}")
            raise
