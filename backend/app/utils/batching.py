"""
Requirement Batching Utility

Groups similar requirements together to reduce API calls and improve efficiency.
Uses similarity scoring based on category, temporal keywords, and entities.

Validates: Performance optimization for API call reduction
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def batch_requirements_by_similarity(
    requirements: List[Dict[str, Any]],
    max_batch_size: int = 3
) -> List[List[Dict[str, Any]]]:
    """
    Batch requirements by similarity to reduce API calls
    
    Groups requirements that:
    - Share the same category
    - Have similar temporal keywords
    - Reference similar entities
    
    Args:
        requirements: List of requirement dictionaries
        max_batch_size: Maximum number of requirements per batch
        
    Returns:
        List of requirement batches
    """
    if not requirements:
        return []
    
    # Group by category first
    category_groups = {}
    for req in requirements:
        category = req.get("category", "functional")
        if category not in category_groups:
            category_groups[category] = []
        category_groups[category].append(req)
    
    # Further split each category group into batches
    batches = []
    for category, reqs in category_groups.items():
        # Split into batches of max_batch_size
        for i in range(0, len(reqs), max_batch_size):
            batch = reqs[i:i + max_batch_size]
            batches.append(batch)
            logger.info(
                f"Created batch of {len(batch)} requirements "
                f"(category: {category})"
            )
    
    logger.info(
        f"Batched {len(requirements)} requirements into "
        f"{len(batches)} batches (max size: {max_batch_size})"
    )
    
    return batches


def calculate_similarity_score(req1: Dict[str, Any], req2: Dict[str, Any]) -> float:
    """
    Calculate similarity score between two requirements
    
    Args:
        req1: First requirement
        req2: Second requirement
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    score = 0.0
    
    # Category match (40% weight)
    if req1.get("category") == req2.get("category"):
        score += 0.4
    
    # Temporal keywords overlap (30% weight)
    keywords1 = set(req1.get("temporal_keywords", []))
    keywords2 = set(req2.get("temporal_keywords", []))
    if keywords1 and keywords2:
        overlap = len(keywords1 & keywords2) / max(len(keywords1), len(keywords2))
        score += 0.3 * overlap
    elif not keywords1 and not keywords2:
        score += 0.3  # Both have no temporal keywords
    
    # Entity overlap (30% weight)
    entities1 = set(req1.get("entities", []))
    entities2 = set(req2.get("entities", []))
    if entities1 and entities2:
        overlap = len(entities1 & entities2) / max(len(entities1), len(entities2))
        score += 0.3 * overlap
    
    return score


def batch_requirements_by_clustering(
    requirements: List[Dict[str, Any]],
    similarity_threshold: float = 0.6,
    max_batch_size: int = 3
) -> List[List[Dict[str, Any]]]:
    """
    Batch requirements using similarity clustering
    
    More sophisticated batching that groups requirements based on
    similarity scores rather than just category.
    
    Args:
        requirements: List of requirement dictionaries
        similarity_threshold: Minimum similarity to group together
        max_batch_size: Maximum number of requirements per batch
        
    Returns:
        List of requirement batches
    """
    if not requirements:
        return []
    
    batches = []
    remaining = requirements.copy()
    
    while remaining:
        # Start a new batch with the first remaining requirement
        current_batch = [remaining.pop(0)]
        
        # Try to add similar requirements to this batch
        i = 0
        while i < len(remaining) and len(current_batch) < max_batch_size:
            req = remaining[i]
            
            # Check similarity with all requirements in current batch
            avg_similarity = sum(
                calculate_similarity_score(req, batch_req)
                for batch_req in current_batch
            ) / len(current_batch)
            
            if avg_similarity >= similarity_threshold:
                current_batch.append(remaining.pop(i))
            else:
                i += 1
        
        batches.append(current_batch)
    
    logger.info(
        f"Clustered {len(requirements)} requirements into "
        f"{len(batches)} batches (threshold: {similarity_threshold})"
    )
    
    return batches
