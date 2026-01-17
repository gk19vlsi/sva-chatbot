"""
SystemVerilog Parser Utilities

Provides utilities for parsing SystemVerilog RTL code.
Extracts modules, ports, signals, and other structural information using regex patterns.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class SystemVerilogParser:
    """
    Parser for SystemVerilog RTL code using regex patterns.
    
    Extracts:
    - Module definitions
    - Port declarations (input, output, inout)
    - Signal declarations (wire, reg, logic)
    """
    
    def __init__(self):
        """Initialize the SystemVerilog parser."""
        pass
    
    def parse_file(self, file_path: str) -> Tuple[Dict[str, Any], bool]:
        """
        Parse a SystemVerilog file and extract structural information.
        
        Args:
            file_path: Path to the SystemVerilog file
            
        Returns:
            Tuple of (parsed_data, success)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.parse_code(source_code)
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return {}, False
    
    def parse_code(self, source_code: str) -> Tuple[Dict[str, Any], bool]:
        """
        Parse SystemVerilog source code and extract structural information.
        
        Args:
            source_code: SystemVerilog source code string
            
        Returns:
            Tuple of (parsed_data, success)
        """
        try:
            # Extract modules
            modules = self._extract_modules(source_code)
            
            if not modules:
                logger.warning("No modules found in source code")
                return {"modules": []}, False
            
            parsed_data = {
                "modules": modules,
                "source_code": source_code
            }
            
            return parsed_data, True
            
        except Exception as e:
            logger.error(f"Error parsing SystemVerilog code: {str(e)}")
            return {}, False
    
    def _extract_modules(self, source_code: str) -> List[Dict[str, Any]]:
        """
        Extract all module definitions from the source code.
        
        Args:
            source_code: Source code string
            
        Returns:
            List of module dictionaries
        """
        modules = []
        
        # Pattern to match module declarations
        module_pattern = r'module\s+(\w+)\s*(?:#\([^)]*\))?\s*\((.*?)\);(.*?)endmodule'
        
        for match in re.finditer(module_pattern, source_code, re.DOTALL):
            module_name = match.group(1)
            ports_text = match.group(2)
            body_text = match.group(3)
            
            # Extract ports
            ports = self._extract_ports(ports_text)
            
            # Extract internal signals
            signals = self._extract_signals(body_text)
            
            # Combine ports and signals
            all_signals = ports + signals
            
            # Calculate line numbers
            start_pos = match.start()
            start_line = source_code[:start_pos].count('\n') + 1
            end_pos = match.end()
            end_line = source_code[:end_pos].count('\n') + 1
            
            module_info = {
                "name": module_name,
                "ports": ports,
                "signals": all_signals,
                "start_line": start_line,
                "end_line": end_line
            }
            
            modules.append(module_info)
        
        return modules
    
    def _extract_ports(self, ports_text: str) -> List[Dict[str, Any]]:
        """
        Extract port declarations from module port list.
        
        Args:
            ports_text: Text containing port declarations
            
        Returns:
            List of port dictionaries
        """
        ports = []
        
        # Pattern to match port declarations
        port_pattern = r'(input|output|inout)\s+(logic|wire|reg)?\s*(\[.*?\])?\s*(\w+)'
        
        for match in re.finditer(port_pattern, ports_text):
            direction = match.group(1)
            data_type = match.group(2) or "logic"
            port_name = match.group(4)
            
            ports.append({
                "name": port_name,
                "direction": direction,
                "type": data_type,
                "is_port": True
            })
        
        return ports
    
    def _extract_signals(self, body_text: str) -> List[Dict[str, Any]]:
        """
        Extract internal signal declarations from module body.
        
        Args:
            body_text: Module body text
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Pattern to match signal declarations
        signal_pattern = r'(logic|wire|reg)\s*(\[.*?\])?\s*(\w+)\s*;'
        
        for match in re.finditer(signal_pattern, body_text):
            data_type = match.group(1)
            signal_name = match.group(3)
            
            signals.append({
                "name": signal_name,
                "type": data_type,
                "is_port": False
            })
        
        return signals


def detect_clocks_and_resets(signals: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    Detect clock and reset signals based on naming conventions.
    
    Args:
        signals: List of signal dictionaries
        
    Returns:
        Tuple of (clock_signals, reset_signals)
    """
    clocks = []
    resets = []
    
    clock_patterns = [r'clk', r'clock', r'ck']
    reset_patterns = [r'rst', r'reset', r'rstn', r'rst_n']
    
    for signal in signals:
        signal_name = signal.get("name", "").lower()
        
        # Check for clock patterns
        for pattern in clock_patterns:
            if re.search(pattern, signal_name):
                clocks.append(signal["name"])
                break
        
        # Check for reset patterns
        for pattern in reset_patterns:
            if re.search(pattern, signal_name):
                resets.append(signal["name"])
                break
    
    return clocks, resets
