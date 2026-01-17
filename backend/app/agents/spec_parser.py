"""
Specification Parser Agent

Extracts and structures requirements from natural language specifications.
Uses LLM to parse requirements, identify temporal keywords, categorize, and extract entities.
Uses advanced prompt engineering with few-shot examples and chain-of-thought reasoning.
"""
from typing import List, Dict, Any
from app.agents.base import Agent, PipelineContext, AgentResult
from app.agents.prompt_templates import SpecificationParserPrompts
from app.clients.groq_client import GroqClient
from bson import ObjectId
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class SpecificationParserAgent(Agent):
    """
    Agent responsible for parsing specification documents and extracting structured requirements.
    
    Capabilities:
    - Segment specification text into individual requirements
    - Extract temporal keywords (e.g., "within", "before", "after", "always")
    - Categorize requirements (functional, timing, safety, liveness)
    - Extract entity names (signals, modules, states)
    """
    
    def __init__(self, groq_client: GroqClient, db):
        super().__init__("SpecificationParser", groq_client, db)
        
        # Temporal keywords to detect
        self.temporal_keywords = [
            "within", "before", "after", "until", "always", "eventually",
            "never", "whenever", "immediately", "next", "cycles", "clock",
            "simultaneously", "followed by", "preceded by", "during"
        ]
        
        # Requirement categories
        self.categories = [
            "functional",  # Basic behavior requirements
            "timing",      # Temporal/timing constraints
            "safety",      # Safety properties (something bad never happens)
            "liveness"     # Liveness properties (something good eventually happens)
        ]
    
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute specification parsing.
        
        Args:
            context: Pipeline context containing specification text
            
        Returns:
            AgentResult with parsed requirements
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract specification text from context
            spec_text = context.data.get("specification_text", "")
            if not spec_text:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No specification text provided in context"
                )
            
            logger.info(f"Parsing specification ({len(spec_text)} characters)")
            
            # Step 1: Segment specification into requirements using LLM
            requirements = await self._segment_requirements(spec_text)
            
            if not requirements:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No requirements extracted from specification"
                )
            
            logger.info(f"Extracted {len(requirements)} requirements")
            
            # Step 2: Process requirements in batches for efficiency
            from app.utils.batching import batch_requirements_by_similarity
            
            # Batch requirements by category (reduces API calls)
            requirement_batches = batch_requirements_by_similarity(
                [{"text": req, "index": idx + 1} for idx, req in enumerate(requirements)],
                max_batch_size=3
            )
            
            processed_requirements = []
            for batch in requirement_batches:
                # Process batch together
                batch_results = await self._process_requirement_batch(batch)
                processed_requirements.extend(batch_results)
            
            # Step 3: Store in database
            spec_id = context.data.get("specification_id")
            if spec_id:
                await self._store_requirements(spec_id, processed_requirements)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "requirements": processed_requirements,
                    "total_requirements": len(processed_requirements),
                    "execution_time": execution_time
                },
                metadata={
                    "requirements_count": len(processed_requirements),
                    "categories": self._count_categories(processed_requirements)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in SpecificationParser: {str(e)}")
            return AgentResult(
                success=False,
                agent_name=self.name,
                data={},
                error=str(e)
            )
    
    async def _segment_requirements(self, spec_text: str) -> List[str]:
        """
        Segment specification text into individual requirements using LLM with advanced prompts.
        
        Args:
            spec_text: Raw specification text
            
        Returns:
            List of requirement strings
        """
        # Use advanced prompt template with few-shot examples
        system_prompt = SpecificationParserPrompts.get_system_prompt()
        user_prompt = SpecificationParserPrompts.get_segmentation_prompt(spec_text)
        
        try:
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            # Parse JSON response
            result = json.loads(response)
            requirements = result.get("requirements", [])
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error segmenting requirements: {str(e)}")
            # Fallback: split by newlines and filter
            lines = spec_text.split('\n')
            requirements = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20]
            return requirements
    
    async def _process_requirement(self, requirement_text: str, req_number: int) -> Dict[str, Any]:
        """
        Process a single requirement to extract metadata.
        
        Args:
            requirement_text: The requirement text
            req_number: Requirement number
            
        Returns:
            Processed requirement dictionary
        """
        # Extract temporal keywords
        temporal_keywords = self._extract_temporal_keywords(requirement_text)
        
        # Categorize requirement and extract entities using LLM
        category, entities = await self._categorize_and_extract_entities(requirement_text)
        
        return {
            "requirement_id": f"REQ-{req_number:03d}",
            "text": requirement_text,
            "category": category,
            "temporal_keywords": temporal_keywords,
            "entities": entities
        }
    
    async def _process_requirement_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of requirements together to reduce API calls.
        
        Args:
            batch: List of requirement dictionaries with 'text' and 'index'
            
        Returns:
            List of processed requirement dictionaries
        """
        if len(batch) == 1:
            # Single requirement, use regular processing
            req = batch[0]
            return [await self._process_requirement(req["text"], req["index"])]
        
        # Process multiple requirements in one API call
        logger.info(f"Processing batch of {len(batch)} requirements together")
        
        # Extract temporal keywords for all (no API call needed)
        results = []
        for req in batch:
            temporal_keywords = self._extract_temporal_keywords(req["text"])
            results.append({
                "text": req["text"],
                "index": req["index"],
                "temporal_keywords": temporal_keywords
            })
        
        # Batch categorization and entity extraction (single API call)
        batch_analysis = await self._batch_categorize_and_extract(results)
        
        # Build final results
        processed = []
        for i, req in enumerate(results):
            analysis = batch_analysis[i] if i < len(batch_analysis) else {}
            processed.append({
                "requirement_id": f"REQ-{req['index']:03d}",
                "text": req["text"],
                "category": analysis.get("category", "functional"),
                "temporal_keywords": req["temporal_keywords"],
                "entities": analysis.get("entities", [])
            })
        
        return processed
    
    def _extract_temporal_keywords(self, text: str) -> List[str]:
        """
        Extract temporal keywords from requirement text.
        
        Args:
            text: Requirement text
            
        Returns:
            List of found temporal keywords
        """
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.temporal_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def _categorize_and_extract_entities(self, requirement_text: str) -> tuple[str, List[str]]:
        """
        Categorize requirement and extract entity names using LLM with chain-of-thought prompting.
        
        Args:
            requirement_text: The requirement text
            
        Returns:
            Tuple of (category, entities)
        """
        # Use advanced prompt template with chain-of-thought reasoning
        system_prompt = SpecificationParserPrompts.get_system_prompt()
        user_prompt = SpecificationParserPrompts.get_categorization_prompt(requirement_text)
        
        try:
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            result = json.loads(response)
            category = result.get("category", "functional")
            entities = result.get("entities", [])
            
            # Validate category
            if category not in self.categories:
                category = "functional"
            
            return category, entities
            
        except Exception as e:
            logger.error(f"Error categorizing requirement: {str(e)}")
            # Fallback: simple heuristics
            text_lower = requirement_text.lower()
            
            if any(kw in text_lower for kw in ["within", "cycles", "before", "after"]):
                category = "timing"
            elif any(kw in text_lower for kw in ["never", "must not", "shall not"]):
                category = "safety"
            elif any(kw in text_lower for kw in ["eventually", "always"]):
                category = "liveness"
            else:
                category = "functional"
            
            # Simple entity extraction: words that look like signal names
            words = requirement_text.split()
            entities = [w.strip('.,;:()[]') for w in words if w.islower() and len(w) > 2][:5]
            
            return category, entities
    
    async def _batch_categorize_and_extract(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch categorize and extract entities for multiple requirements in one API call.
        
        Args:
            requirements: List of requirement dictionaries with 'text'
            
        Returns:
            List of analysis results with 'category' and 'entities'
        """
        # Build batch prompt
        batch_text = "\n\n".join([
            f"Requirement {i+1}: {req['text']}"
            for i, req in enumerate(requirements)
        ])
        
        system_prompt = SpecificationParserPrompts.get_system_prompt()
        user_prompt = f"""Analyze the following {len(requirements)} requirements and for each one, provide:
1. Category (functional, timing, safety, or liveness)
2. List of entity names (signals, modules, states)

{batch_text}

Return a JSON array with one object per requirement:
[
  {{"category": "...", "entities": [...]}},
  ...
]"""
        
        try:
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            result = json.loads(response)
            
            # Ensure we have results for all requirements
            if isinstance(result, list) and len(result) == len(requirements):
                return result
            else:
                logger.warning(f"Batch analysis returned unexpected format, falling back")
                # Fallback to individual processing
                return [
                    {"category": "functional", "entities": []}
                    for _ in requirements
                ]
            
        except Exception as e:
            logger.error(f"Error in batch categorization: {str(e)}")
            # Fallback: return default values
            return [
                {"category": "functional", "entities": []}
                for _ in requirements
            ]
    
    async def _store_requirements(self, spec_id: str, requirements: List[Dict[str, Any]]):
        """
        Store parsed requirements in database.
        
        Args:
            spec_id: Specification document ID
            requirements: List of processed requirements
        """
        try:
            # Update specification document with parsed requirements
            await self.db.specifications.update_one(
                {"_id": ObjectId(spec_id)},
                {
                    "$set": {
                        "parsed_requirements": requirements,
                        "processed": True,
                        "processed_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Stored {len(requirements)} requirements for spec {spec_id}")
            
        except Exception as e:
            logger.error(f"Error storing requirements: {str(e)}")
            raise
    
    def _count_categories(self, requirements: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count requirements by category.
        
        Args:
            requirements: List of requirements
            
        Returns:
            Dictionary of category counts
        """
        counts = {cat: 0 for cat in self.categories}
        for req in requirements:
            category = req.get("category", "functional")
            if category in counts:
                counts[category] += 1
        return counts
