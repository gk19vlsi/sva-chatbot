"""
Context Window Management for Multi-Agent Pipeline

This module provides intelligent context window management to handle long documents
and large RTL files that exceed LLM context limits.

Features:
- Sliding window for long documents
- Context summarization for large inputs
- Relevant context prioritization
- Token counting and estimation

Implements: All agent requirements (context management)
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context window for LLM interactions
    
    Handles:
    - Token estimation and counting
    - Text chunking with sliding windows
    - Context summarization
    - Relevant section extraction
    """
    
    # Approximate token counts (conservative estimates)
    CHARS_PER_TOKEN = 4  # Average characters per token
    MAX_CONTEXT_TOKENS = 30000  # Conservative limit for llama-3.3-70b (32k context)
    RESERVED_TOKENS = 2000  # Reserve for system prompt and response
    
    def __init__(self):
        """Initialize context manager"""
        self.max_input_tokens = self.MAX_CONTEXT_TOKENS - self.RESERVED_TOKENS
        self.max_input_chars = self.max_input_tokens * self.CHARS_PER_TOKEN
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return len(text) // self.CHARS_PER_TOKEN
    
    def fits_in_context(self, text: str, additional_tokens: int = 0) -> bool:
        """
        Check if text fits in context window
        
        Args:
            text: Input text
            additional_tokens: Additional tokens needed (e.g., for prompt template)
            
        Returns:
            True if text fits, False otherwise
        """
        estimated_tokens = self.estimate_tokens(text) + additional_tokens
        return estimated_tokens <= self.max_input_tokens
    
    def truncate_text(self, text: str, max_chars: Optional[int] = None) -> str:
        """
        Truncate text to fit in context window
        
        Args:
            text: Input text
            max_chars: Maximum characters (defaults to max_input_chars)
            
        Returns:
            Truncated text with indicator
        """
        if max_chars is None:
            max_chars = self.max_input_chars
        
        if len(text) <= max_chars:
            return text
        
        truncated = text[:max_chars]
        return truncated + "\n\n... (truncated for length)"
    
    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks (sliding window)
        
        Args:
            text: Input text
            chunk_size: Size of each chunk in characters (defaults to max_input_chars)
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.max_input_chars
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            
            # Avoid infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def chunk_by_sections(
        self,
        text: str,
        section_markers: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Split text into sections based on markers (e.g., headers, requirements)
        
        Args:
            text: Input text
            section_markers: List of regex patterns for section boundaries
            
        Returns:
            List of dictionaries with 'title' and 'content'
        """
        if section_markers is None:
            # Default markers for common document structures
            section_markers = [
                r'^#+\s+(.+)$',  # Markdown headers
                r'^(\d+\.?\s+.+)$',  # Numbered sections
                r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headers
            ]
        
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        
        lines = text.split('\n')
        
        for line in lines:
            # Check if line matches any section marker
            is_section_start = False
            for pattern in section_markers:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous section if it has content
                    if current_section["content"].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "title": match.group(1) if match.lastindex else line.strip(),
                        "content": ""
                    }
                    is_section_start = True
                    break
            
            if not is_section_start:
                current_section["content"] += line + "\n"
        
        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def prioritize_context(
        self,
        sections: List[Dict[str, str]],
        query: str,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Prioritize and select most relevant sections based on query
        
        Args:
            sections: List of section dictionaries
            query: Query or requirement to match against
            max_chars: Maximum total characters
            
        Returns:
            Combined text from most relevant sections
        """
        if max_chars is None:
            max_chars = self.max_input_chars
        
        # Score sections by relevance to query
        query_terms = set(query.lower().split())
        scored_sections = []
        
        for section in sections:
            title = section["title"].lower()
            content = section["content"].lower()
            
            # Calculate relevance score
            title_matches = sum(1 for term in query_terms if term in title)
            content_matches = sum(1 for term in query_terms if term in content)
            
            score = title_matches * 3 + content_matches  # Weight title matches higher
            
            scored_sections.append((score, section))
        
        # Sort by score (descending)
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        # Select sections until we reach max_chars
        selected_text = ""
        for score, section in scored_sections:
            section_text = f"\n## {section['title']}\n{section['content']}\n"
            
            if len(selected_text) + len(section_text) <= max_chars:
                selected_text += section_text
            else:
                # Add partial section if there's room
                remaining = max_chars - len(selected_text)
                if remaining > 100:  # Only add if meaningful amount remains
                    selected_text += section_text[:remaining] + "\n... (truncated)"
                break
        
        return selected_text
    
    def summarize_for_context(
        self,
        text: str,
        target_length: int = 1000
    ) -> str:
        """
        Create a summary of text for context (simple extractive approach)
        
        Args:
            text: Input text to summarize
            target_length: Target length in characters
            
        Returns:
            Summarized text
        """
        if len(text) <= target_length:
            return text
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return self.truncate_text(text, target_length)
        
        # Calculate how many sentences we can fit
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) + 2 <= target_length:
                summary += sentence + ". "
            else:
                break
        
        if not summary:
            # If even first sentence is too long, truncate it
            summary = sentences[0][:target_length] + "..."
        
        return summary.strip()
    
    def prepare_specification_context(
        self,
        spec_text: str,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Prepare specification text for LLM context
        
        Applies intelligent chunking and prioritization
        
        Args:
            spec_text: Full specification text
            max_chars: Maximum characters to return
            
        Returns:
            Prepared context text
        """
        if max_chars is None:
            max_chars = self.max_input_chars
        
        # If it fits, return as-is
        if len(spec_text) <= max_chars:
            return spec_text
        
        # Try to split by sections and prioritize
        sections = self.chunk_by_sections(spec_text)
        
        if len(sections) > 1:
            # Keep all sections but truncate content if needed
            prepared = ""
            chars_per_section = max_chars // len(sections)
            
            for section in sections:
                section_text = f"\n## {section['title']}\n"
                content = section['content']
                
                if len(content) > chars_per_section:
                    content = content[:chars_per_section] + "\n... (section truncated)"
                
                section_text += content
                prepared += section_text
            
            return prepared
        else:
            # No clear sections, just truncate
            return self.truncate_text(spec_text, max_chars)
    
    def prepare_rtl_context(
        self,
        rtl_code: str,
        focus_module: Optional[str] = None,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Prepare RTL code for LLM context
        
        Args:
            rtl_code: Full RTL source code
            focus_module: Specific module to focus on (if known)
            max_chars: Maximum characters to return
            
        Returns:
            Prepared context text
        """
        if max_chars is None:
            max_chars = self.max_input_chars
        
        # If it fits, return as-is
        if len(rtl_code) <= max_chars:
            return rtl_code
        
        # If focus module specified, try to extract just that module
        if focus_module:
            module_code = self._extract_module(rtl_code, focus_module)
            if module_code and len(module_code) <= max_chars:
                return module_code
        
        # Otherwise, truncate with indication
        return self.truncate_text(rtl_code, max_chars)
    
    def _extract_module(self, rtl_code: str, module_name: str) -> Optional[str]:
        """
        Extract a specific module from RTL code
        
        Args:
            rtl_code: Full RTL source
            module_name: Name of module to extract
            
        Returns:
            Module code or None if not found
        """
        # Look for module definition
        pattern = rf'module\s+{re.escape(module_name)}\s*[^;]*;.*?endmodule'
        match = re.search(pattern, rtl_code, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(0)
        
        return None
    
    def prepare_multi_document_context(
        self,
        documents: List[Dict[str, str]],
        query: str,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Prepare context from multiple documents with prioritization
        
        Args:
            documents: List of documents with 'title' and 'content'
            query: Query to prioritize against
            max_chars: Maximum total characters
            
        Returns:
            Combined context from most relevant documents
        """
        if max_chars is None:
            max_chars = self.max_input_chars
        
        # Score documents by relevance
        query_terms = set(query.lower().split())
        scored_docs = []
        
        for doc in documents:
            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()
            
            # Calculate relevance score
            title_matches = sum(1 for term in query_terms if term in title)
            content_matches = sum(1 for term in query_terms if term in content)
            
            score = title_matches * 5 + content_matches
            scored_docs.append((score, doc))
        
        # Sort by relevance
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Combine documents until we reach limit
        combined = ""
        for score, doc in scored_docs:
            doc_text = f"\n### {doc.get('title', 'Document')}\n{doc.get('content', '')}\n"
            
            if len(combined) + len(doc_text) <= max_chars:
                combined += doc_text
            else:
                # Add partial document
                remaining = max_chars - len(combined)
                if remaining > 200:
                    combined += doc_text[:remaining] + "\n... (truncated)"
                break
        
        return combined


# Global context manager instance
context_manager = ContextManager()


# Convenience functions
def estimate_tokens(text: str) -> int:
    """Estimate token count for text"""
    return context_manager.estimate_tokens(text)


def fits_in_context(text: str, additional_tokens: int = 0) -> bool:
    """Check if text fits in context window"""
    return context_manager.fits_in_context(text, additional_tokens)


def truncate_text(text: str, max_chars: Optional[int] = None) -> str:
    """Truncate text to fit in context"""
    return context_manager.truncate_text(text, max_chars)


def chunk_text(text: str, chunk_size: Optional[int] = None, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    return context_manager.chunk_text(text, chunk_size, overlap)


def prepare_specification_context(spec_text: str, max_chars: Optional[int] = None) -> str:
    """Prepare specification for LLM context"""
    return context_manager.prepare_specification_context(spec_text, max_chars)


def prepare_rtl_context(rtl_code: str, focus_module: Optional[str] = None, 
                       max_chars: Optional[int] = None) -> str:
    """Prepare RTL code for LLM context"""
    return context_manager.prepare_rtl_context(rtl_code, focus_module, max_chars)


__all__ = [
    'ContextManager',
    'context_manager',
    'estimate_tokens',
    'fits_in_context',
    'truncate_text',
    'chunk_text',
    'prepare_specification_context',
    'prepare_rtl_context'
]
