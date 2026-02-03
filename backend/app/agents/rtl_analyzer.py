"""
RTL Analyzer Agent

Analyzes SystemVerilog RTL code to extract structural and semantic information.
Uses parser for syntax analysis and LLM for semantic understanding.
Uses advanced prompt engineering with structured output and few-shot examples.
"""
from typing import List, Dict, Any
from app.agents.base import Agent, PipelineContext, AgentResult
from app.agents.prompt_templates import RTLAnalyzerPrompts
from app.clients.base import LLMClient
from app.utils.sv_parser import SystemVerilogParser, detect_clocks_and_resets
from bson import ObjectId
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class RTLAnalyzerAgent(Agent):
    """
    Agent responsible for analyzing RTL designs and extracting structural/semantic information.
    
    Capabilities:
    - Parse SystemVerilog code to extract modules, ports, signals
    - Detect clock and reset signals
    - Identify state machines using LLM
    - Build signal dependency graphs
    - Recognize common protocol patterns (handshake, FIFO, etc.)
    """
    
    def __init__(self, llm_client: LLMClient, db):
        super().__init__("RTLAnalyzer", llm_client, db)
        self.parser = SystemVerilogParser()
    
    async def execute(self, context: PipelineContext) -> AgentResult:
        """
        Execute RTL analysis.
        
        Args:
            context: Pipeline context containing RTL source code
            
        Returns:
            AgentResult with analysis data
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract RTL source code from context
            rtl_code = context.data.get("rtl_code", "")
            if not rtl_code:
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="No RTL code provided in context"
                )
            
            logger.info(f"Analyzing RTL code ({len(rtl_code)} characters)")
            
            # Step 1: Parse RTL code to extract structure
            parsed_data, parse_success = self.parser.parse_code(rtl_code)
            
            if not parse_success or not parsed_data.get("modules"):
                return AgentResult(
                    success=False,
                    agent_name=self.name,
                    data={},
                    error="Failed to parse RTL code or no modules found"
                )
            
            modules = parsed_data["modules"]
            logger.info(f"Parsed {len(modules)} modules")
            
            # Step 2: Analyze each module
            analyzed_modules = []
            for module in modules:
                analyzed_module = await self._analyze_module(module, rtl_code)
                analyzed_modules.append(analyzed_module)
            
            # Step 3: Determine default clock and reset
            default_clock, default_reset = self._determine_defaults(analyzed_modules)
            
            # Step 4: Store in database
            rtl_id = context.data.get("rtl_design_id")
            if rtl_id:
                await self._store_analysis(rtl_id, analyzed_modules, default_clock, default_reset)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "rtl_modules": analyzed_modules,  # Changed from "modules" to "rtl_modules"
                    "modules": analyzed_modules,  # Keep for backward compatibility
                    "default_clock": default_clock,
                    "default_reset": default_reset,
                    "execution_time": execution_time
                },
                metadata={
                    "module_count": len(analyzed_modules),
                    "total_signals": sum(len(m.get("signals", [])) for m in analyzed_modules)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in RTLAnalyzer: {str(e)}")
            return AgentResult(
                success=False,
                agent_name=self.name,
                data={},
                error=str(e)
            )
    
    async def _analyze_module(self, module: Dict[str, Any], rtl_code: str) -> Dict[str, Any]:
        """
        Analyze a single module to extract semantic information.
        
        Args:
            module: Parsed module data
            rtl_code: Full RTL source code
            
        Returns:
            Enhanced module dictionary with analysis
        """
        module_name = module.get("name", "")
        signals = module.get("signals", [])
        
        # Detect clocks and resets
        clocks, resets = detect_clocks_and_resets(signals)
        
        # Extract module code snippet
        start_line = module.get("start_line", 1)
        end_line = module.get("end_line", 1)
        lines = rtl_code.split('\n')
        module_code = '\n'.join(lines[start_line-1:end_line])
        
        # Use LLM for semantic analysis
        semantic_info = await self._semantic_analysis(module_name, module_code, signals)
        
        # Build signal dependency graph
        dependencies = self._build_dependencies(module_code, signals)
        
        return {
            "name": module_name,
            "signals": signals,
            "ports": module.get("ports", []),
            "clocks": clocks,
            "resets": resets,
            "state_machines": semantic_info.get("state_machines", []),
            "protocols": semantic_info.get("protocols", []),
            "dependencies": dependencies,
            "start_line": start_line,
            "end_line": end_line
        }
    
    async def _semantic_analysis(self, module_name: str, module_code: str, 
                                 signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform semantic analysis using LLM with advanced prompts.
        
        Args:
            module_name: Name of the module
            module_code: Module source code
            signals: List of signals
            
        Returns:
            Dictionary with semantic information
        """
        signal_names = [s.get("name", "") for s in signals]
        
        # Use advanced prompt template with structured reasoning
        system_prompt = RTLAnalyzerPrompts.get_system_prompt()
        user_prompt = RTLAnalyzerPrompts.get_semantic_analysis_prompt(
            module_name, module_code, signal_names
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
            logger.error(f"Error in semantic analysis: {str(e)}")
            return {"state_machines": [], "protocols": []}
    
    def _build_dependencies(self, module_code: str, signals: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Build signal dependency graph (simple version).
        
        Args:
            module_code: Module source code
            signals: List of signals
            
        Returns:
            Dictionary mapping signals to their dependencies
        """
        dependencies = {}
        
        # Simple heuristic: look for assignments
        for signal in signals:
            signal_name = signal.get("name", "")
            deps = []
            
            # Look for lines where this signal is assigned
            for line in module_code.split('\n'):
                if f"{signal_name} <=" in line or f"{signal_name} =" in line:
                    # Extract other signal names from the right side
                    for other_signal in signals:
                        other_name = other_signal.get("name", "")
                        if other_name != signal_name and other_name in line:
                            deps.append(other_name)
            
            if deps:
                dependencies[signal_name] = list(set(deps))
        
        return dependencies
    
    def _determine_defaults(self, modules: List[Dict[str, Any]]) -> tuple[str, str]:
        """
        Determine default clock and reset signals across all modules.
        
        Args:
            modules: List of analyzed modules
            
        Returns:
            Tuple of (default_clock, default_reset)
        """
        # Collect all clocks and resets
        all_clocks = []
        all_resets = []
        
        for module in modules:
            all_clocks.extend(module.get("clocks", []))
            all_resets.extend(module.get("resets", []))
        
        # Find most common clock
        default_clock = "clk"  # fallback
        if all_clocks:
            from collections import Counter
            clock_counts = Counter(all_clocks)
            default_clock = clock_counts.most_common(1)[0][0]
        
        # Find most common reset
        default_reset = "rst_n"  # fallback
        if all_resets:
            from collections import Counter
            reset_counts = Counter(all_resets)
            default_reset = reset_counts.most_common(1)[0][0]
        
        return default_clock, default_reset
    
    async def _store_analysis(self, rtl_id: str, modules: List[Dict[str, Any]], 
                              default_clock: str, default_reset: str):
        """
        Store RTL analysis in database.
        
        Args:
            rtl_id: RTL design document ID
            modules: Analyzed modules
            default_clock: Default clock signal
            default_reset: Default reset signal
        """
        try:
            # Update RTL design document with analysis
            await self.db.rtl_designs.update_one(
                {"_id": ObjectId(rtl_id)},
                {
                    "$set": {
                        "analysis": {
                            "modules": modules,
                            "default_clock": default_clock,
                            "default_reset": default_reset
                        },
                        "processed": True,
                        "processed_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Stored analysis for RTL design {rtl_id}")
            
        except Exception as e:
            logger.error(f"Error storing RTL analysis: {str(e)}")
            raise
