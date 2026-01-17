"""
Alignment Agent

Maps requirements to RTL signals and identifies gaps between specification and implementation.
Uses LLM to understand semantic relationships and calculate confidence scores.
Uses advanced prompt engineering with confidence scoring and ambiguity detection.
"""
from typing import List, Dict, Any, Optional
from app.agents.base import Agent, PipelineContext, AgentResult
from app.agents.prompt_templates import AlignmentPrompts
from app.clients.groq_client import GroqClient
from bson import ObjectId
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class AlignmentAgent(Agent):
    """
    Agent responsible for aligning requirements with RTL implementation.
    
    Capabilities:
    - Map requirement entities to RTL signals
    - Calculate confidence scores for alignments
    - Identify missing implementations
    - Generate clarification questions for ambiguities
    - Store alignment data for traceability
    """
    
    def __init__(self, groq_client: GroqClient, db):
        super().__init__("Alignment", groq_client, db)
    
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute requirement-RTL alignment.
        
        Args:
            context: Pipeline context containing requirements and RTL analysis
            
        Returns:
            AgentResult with alignment data
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract requirements and RTL analysis from context
            requirements = context.data.get("requirements", [])
            rtl_modules = context.data.get("rtl_modules", [])
            
            if not requirements:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No requirements provided in context"
                )
            
            if not rtl_modules:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No RTL modules provided in context"
                )
            
            logger.info(f"Aligning {len(requirements)} requirements with {len(rtl_modules)} modules")
            
            # Step 1: Align each requirement with RTL
            alignments = []
            for req in requirements:
                alignment = await self._align_requirement(req, rtl_modules)
                alignments.append(alignment)
            
            # Step 2: Identify missing implementations
            missing_implementations = self._identify_missing(alignments)
            
            # Step 3: Generate clarification questions
            clarifications = self._generate_clarifications(alignments)
            
            # Step 4: Store alignments in database
            project_id = context.project_id
            if project_id:
                await self._store_alignments(project_id, alignments)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate statistics
            high_confidence = sum(1 for a in alignments if a.get("confidence", 0) >= 0.8)
            low_confidence = sum(1 for a in alignments if a.get("confidence", 0) < 0.5)
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "alignments": alignments,
                    "missing_implementations": missing_implementations,
                    "clarifications": clarifications,
                    "execution_time": execution_time
                },
                metadata={
                    "total_alignments": len(alignments),
                    "high_confidence": high_confidence,
                    "low_confidence": low_confidence,
                    "missing_count": len(missing_implementations)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Alignment agent: {str(e)}")
            return AgentResult(
                success=False,
                agent_name=self.name,
                data={},
                error=str(e)
            )
    
    async def _align_requirement(self, requirement: Dict[str, Any], 
                                 rtl_modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Align a single requirement with RTL signals.
        
        Args:
            requirement: Requirement dictionary
            rtl_modules: List of RTL module dictionaries
            
        Returns:
            Alignment dictionary with mapped signals and confidence
        """
        req_id = requirement.get("requirement_id", "")
        req_text = requirement.get("text", "")
        req_entities = requirement.get("entities", [])
        
        # Collect all signals from all modules
        all_signals = []
        for module in rtl_modules:
            module_name = module.get("name", "")
            for signal in module.get("signals", []):
                all_signals.append({
                    "name": signal.get("name", ""),
                    "module": module_name,
                    "type": signal.get("type", ""),
                    "direction": signal.get("direction", "")
                })
        
        # Use LLM to map requirement entities to RTL signals
        mapping = await self._map_entities_to_signals(req_text, req_entities, all_signals)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(req_entities, mapping)
        
        return {
            "requirement_id": req_id,
            "requirement_text": req_text,
            "entities": req_entities,
            "mapped_signals": mapping.get("signals", []),
            "confidence": confidence,
            "notes": mapping.get("notes", ""),
            "ambiguities": mapping.get("ambiguities", [])
        }
    
    async def _map_entities_to_signals(self, req_text: str, entities: List[str], 
                                       signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use LLM to map requirement entities to RTL signals with advanced prompts.
        
        Args:
            req_text: Requirement text
            entities: List of entity names from requirement
            signals: List of available RTL signals
            
        Returns:
            Mapping dictionary
        """
        # Use advanced prompt template with confidence scoring
        system_prompt = AlignmentPrompts.get_system_prompt()
        user_prompt = AlignmentPrompts.get_mapping_prompt(req_text, entities, signals)
        
        try:
            response = await self.call_groq(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )
            
            result = json.loads(response)
            return result
            
        except Exception as e:
            logger.error(f"Error mapping entities to signals: {str(e)}")
            # Fallback: simple name matching
            mapped_signals = []
            for entity in entities:
                for signal in signals:
                    if entity.lower() in signal["name"].lower() or signal["name"].lower() in entity.lower():
                        mapped_signals.append({
                            "entity": entity,
                            "rtl_signal": signal["name"],
                            "module": signal["module"],
                            "confidence": 0.6
                        })
                        break
            
            return {
                "signals": mapped_signals,
                "ambiguities": ["Automatic mapping used due to LLM error"],
                "notes": "Fallback mapping based on name similarity"
            }
    
    def _calculate_confidence(self, entities: List[str], mapping: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the alignment.
        
        Args:
            entities: List of requirement entities
            mapping: Mapping result
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not entities:
            return 0.5  # Neutral confidence if no entities
        
        mapped_signals = mapping.get("signals", [])
        
        # Calculate percentage of entities that were mapped
        mapped_entities = set(s.get("entity", "") for s in mapped_signals)
        coverage = len(mapped_entities) / len(entities) if entities else 0
        
        # Average confidence from individual mappings
        if mapped_signals:
            avg_mapping_confidence = sum(s.get("confidence", 0.5) for s in mapped_signals) / len(mapped_signals)
        else:
            avg_mapping_confidence = 0.0
        
        # Penalty for ambiguities
        ambiguity_penalty = 0.1 * len(mapping.get("ambiguities", []))
        
        # Final confidence
        confidence = (coverage * 0.5 + avg_mapping_confidence * 0.5) - ambiguity_penalty
        
        return max(0.0, min(1.0, confidence))
    
    def _identify_missing(self, alignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify requirements with missing or weak implementations.
        
        Args:
            alignments: List of alignment dictionaries
            
        Returns:
            List of missing implementation descriptions
        """
        missing = []
        
        for alignment in alignments:
            confidence = alignment.get("confidence", 0)
            mapped_signals = alignment.get("mapped_signals", [])
            
            # Low confidence or no mappings indicate potential missing implementation
            if confidence < 0.5 or len(mapped_signals) == 0:
                missing.append({
                    "requirement_id": alignment.get("requirement_id", ""),
                    "requirement_text": alignment.get("requirement_text", ""),
                    "reason": "Low confidence alignment" if confidence < 0.5 else "No signals mapped",
                    "confidence": confidence
                })
        
        return missing
    
    def _generate_clarifications(self, alignments: List[Dict[str, Any]]) -> List[str]:
        """
        Generate clarification questions for ambiguous alignments.
        
        Args:
            alignments: List of alignment dictionaries
            
        Returns:
            List of clarification questions
        """
        clarifications = []
        
        for alignment in alignments:
            ambiguities = alignment.get("ambiguities", [])
            req_id = alignment.get("requirement_id", "")
            
            for ambiguity in ambiguities:
                question = f"[{req_id}] {ambiguity}"
                clarifications.append(question)
        
        return clarifications
    
    async def _store_alignments(self, project_id: str, alignments: List[Dict[str, Any]]):
        """
        Store alignment data in database.
        
        Args:
            project_id: Project ID
            alignments: List of alignment dictionaries
        """
        try:
            # Store alignments as a collection or embedded in project
            for alignment in alignments:
                alignment_doc = {
                    "project_id": ObjectId(project_id),
                    "requirement_id": alignment.get("requirement_id", ""),
                    "requirement_text": alignment.get("requirement_text", ""),
                    "mapped_signals": alignment.get("mapped_signals", []),
                    "confidence": alignment.get("confidence", 0),
                    "ambiguities": alignment.get("ambiguities", []),
                    "created_at": datetime.utcnow()
                }
                
                # Upsert alignment (update if exists, insert if not)
                await self.db.alignments.update_one(
                    {
                        "project_id": ObjectId(project_id),
                        "requirement_id": alignment.get("requirement_id", "")
                    },
                    {"$set": alignment_doc},
                    upsert=True
                )
            
            logger.info(f"Stored {len(alignments)} alignments for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error storing alignments: {str(e)}")
            raise
