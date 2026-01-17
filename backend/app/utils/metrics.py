"""
Performance Metrics Tracking

Tracks and aggregates performance metrics for:
- API response times
- Agent execution times
- Database query times
- LLM API latency

Implements Requirement 16.5: Agent performance metrics tracking
"""
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Container for metric measurements"""
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    
    def add(self, value: float):
        """Add a measurement"""
        self.values.append(value)
        self.timestamps.append(datetime.utcnow())
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistics for the metric"""
        if not self.values:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0
            }
        
        sorted_values = sorted(self.values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": min(sorted_values),
            "max": max(sorted_values),
            "mean": statistics.mean(sorted_values),
            "median": statistics.median(sorted_values),
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0
        }
    
    def cleanup_old(self, max_age_hours: int = 24):
        """Remove measurements older than max_age_hours"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Find indices to keep
        keep_indices = [
            i for i, ts in enumerate(self.timestamps)
            if ts > cutoff
        ]
        
        # Keep only recent measurements
        self.values = [self.values[i] for i in keep_indices]
        self.timestamps = [self.timestamps[i] for i in keep_indices]


class MetricsCollector:
    """
    Collects and aggregates performance metrics
    
    Validates: Requirement 16.5 - Track agent execution times and performance
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self.api_metrics: Dict[str, MetricData] = defaultdict(MetricData)
        self.agent_metrics: Dict[str, MetricData] = defaultdict(MetricData)
        self.database_metrics: Dict[str, MetricData] = defaultdict(MetricData)
        self.llm_metrics: Dict[str, MetricData] = defaultdict(MetricData)
    
    def track_api_request(self, method: str, path: str, duration: float):
        """
        Track API request duration
        
        Args:
            method: HTTP method
            path: Request path
            duration: Request duration in seconds
            
        Validates: Requirement 16.5 - Track API response times
        """
        key = f"{method}:{path}"
        self.api_metrics[key].add(duration)
        
        logger.debug(f"API metric tracked: {key} = {duration:.3f}s")
    
    def track_agent_execution(self, agent_name: str, duration: float):
        """
        Track agent execution duration
        
        Args:
            agent_name: Name of the agent
            duration: Execution duration in seconds
            
        Validates: Requirement 16.5 - Track agent execution times
        """
        self.agent_metrics[agent_name].add(duration)
        
        logger.debug(f"Agent metric tracked: {agent_name} = {duration:.3f}s")
    
    def track_database_query(self, operation: str, collection: str, duration: float):
        """
        Track database query duration
        
        Args:
            operation: Database operation (find, insert, update, delete)
            collection: Collection name
            duration: Query duration in seconds
            
        Validates: Requirement 16.5 - Track database query times
        """
        key = f"{operation}:{collection}"
        self.database_metrics[key].add(duration)
        
        logger.debug(f"Database metric tracked: {key} = {duration:.3f}s")
    
    def track_llm_request(self, model: str, duration: float):
        """
        Track LLM API request duration
        
        Args:
            model: Model name
            duration: Request duration in seconds
            
        Validates: Requirement 16.5 - Track LLM API latency
        """
        self.llm_metrics[model].add(duration)
        
        logger.debug(f"LLM metric tracked: {model} = {duration:.3f}s")
    
    def get_api_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get API metrics statistics
        
        Returns:
            Dictionary of API endpoint metrics
        """
        return {
            endpoint: metric.get_stats()
            for endpoint, metric in self.api_metrics.items()
        }
    
    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get agent execution metrics statistics
        
        Returns:
            Dictionary of agent metrics
        """
        return {
            agent: metric.get_stats()
            for agent, metric in self.agent_metrics.items()
        }
    
    def get_database_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get database query metrics statistics
        
        Returns:
            Dictionary of database operation metrics
        """
        return {
            operation: metric.get_stats()
            for operation, metric in self.database_metrics.items()
        }
    
    def get_llm_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get LLM API metrics statistics
        
        Returns:
            Dictionary of LLM model metrics
        """
        return {
            model: metric.get_stats()
            for model, metric in self.llm_metrics.items()
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics statistics
        
        Returns:
            Dictionary with all metrics categories
        """
        return {
            "api": self.get_api_metrics(),
            "agents": self.get_agent_metrics(),
            "database": self.get_database_metrics(),
            "llm": self.get_llm_metrics()
        }
    
    def cleanup_old_metrics(self, max_age_hours: int = 24):
        """
        Remove metrics older than max_age_hours
        
        Args:
            max_age_hours: Maximum age in hours
        """
        for metric in self.api_metrics.values():
            metric.cleanup_old(max_age_hours)
        
        for metric in self.agent_metrics.values():
            metric.cleanup_old(max_age_hours)
        
        for metric in self.database_metrics.values():
            metric.cleanup_old(max_age_hours)
        
        for metric in self.llm_metrics.values():
            metric.cleanup_old(max_age_hours)
        
        logger.info(f"Cleaned up metrics older than {max_age_hours} hours")
    
    def reset(self):
        """Reset all metrics"""
        self.api_metrics.clear()
        self.agent_metrics.clear()
        self.database_metrics.clear()
        self.llm_metrics.clear()
        
        logger.info("All metrics reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MetricsTimer:
    """
    Context manager for timing operations
    
    Usage:
        with MetricsTimer() as timer:
            # Do work
            pass
        duration = timer.duration
    """
    
    def __init__(self):
        """Initialize timer"""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
    
    def __enter__(self):
        """Start timer"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and calculate duration"""
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        return False


def track_api_request(method: str, path: str, duration: float):
    """
    Track API request metric
    
    Args:
        method: HTTP method
        path: Request path
        duration: Duration in seconds
    """
    metrics_collector.track_api_request(method, path, duration)


def track_agent_execution(agent_name: str, duration: float):
    """
    Track agent execution metric
    
    Args:
        agent_name: Agent name
        duration: Duration in seconds
    """
    metrics_collector.track_agent_execution(agent_name, duration)


def track_database_query(operation: str, collection: str, duration: float):
    """
    Track database query metric
    
    Args:
        operation: Database operation
        collection: Collection name
        duration: Duration in seconds
    """
    metrics_collector.track_database_query(operation, collection, duration)


def track_llm_request(model: str, duration: float):
    """
    Track LLM request metric
    
    Args:
        model: Model name
        duration: Duration in seconds
    """
    metrics_collector.track_llm_request(model, duration)


def get_all_metrics() -> Dict[str, Any]:
    """
    Get all performance metrics
    
    Returns:
        Dictionary with all metrics
    """
    return metrics_collector.get_all_metrics()
