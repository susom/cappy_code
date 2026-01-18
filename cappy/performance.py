"""Performance monitoring for Cappy Code."""

import time
import psutil
from typing import Optional, Dict
from contextlib import contextmanager


class PerformanceMonitor:
    """Monitor performance metrics for Cappy operations."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.process = psutil.Process()
        self.metrics = []
    
    @contextmanager
    def measure(self, operation: str):
        """
        Context manager to measure operation performance.
        
        Args:
            operation: Name of the operation being measured
        
        Yields:
            Dict that will be populated with metrics
        """
        metrics = {
            "operation": operation,
            "start_time": time.time(),
        }
        
        # Capture initial state
        try:
            metrics["start_memory_mb"] = self.process.memory_info().rss / 1024 / 1024
            metrics["start_cpu_percent"] = self.process.cpu_percent()
        except:
            metrics["start_memory_mb"] = 0
            metrics["start_cpu_percent"] = 0
        
        try:
            yield metrics
        finally:
            # Capture final state
            metrics["end_time"] = time.time()
            metrics["duration_ms"] = (metrics["end_time"] - metrics["start_time"]) * 1000
            
            try:
                metrics["end_memory_mb"] = self.process.memory_info().rss / 1024 / 1024
                metrics["memory_delta_mb"] = metrics["end_memory_mb"] - metrics["start_memory_mb"]
                metrics["end_cpu_percent"] = self.process.cpu_percent()
            except:
                metrics["end_memory_mb"] = 0
                metrics["memory_delta_mb"] = 0
                metrics["end_cpu_percent"] = 0
            
            self.metrics.append(metrics)
    
    def get_summary(self) -> Dict:
        """
        Get summary of all measured operations.
        
        Returns:
            Dict with performance summary
        """
        if not self.metrics:
            return {
                "total_operations": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "total_memory_delta_mb": 0,
            }
        
        total_duration = sum(m["duration_ms"] for m in self.metrics)
        total_memory = sum(m.get("memory_delta_mb", 0) for m in self.metrics)
        
        # Group by operation type
        by_operation = {}
        for m in self.metrics:
            op = m["operation"]
            if op not in by_operation:
                by_operation[op] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "total_memory_delta_mb": 0,
                }
            
            by_operation[op]["count"] += 1
            by_operation[op]["total_duration_ms"] += m["duration_ms"]
            by_operation[op]["total_memory_delta_mb"] += m.get("memory_delta_mb", 0)
        
        # Calculate averages
        for op, stats in by_operation.items():
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
            stats["avg_memory_delta_mb"] = stats["total_memory_delta_mb"] / stats["count"]
        
        return {
            "total_operations": len(self.metrics),
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / len(self.metrics),
            "total_memory_delta_mb": total_memory,
            "by_operation": by_operation,
        }
    
    def clear(self):
        """Clear all metrics."""
        self.metrics = []


# Global performance monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


@contextmanager
def measure_performance(operation: str):
    """
    Convenience function to measure operation performance.
    
    Args:
        operation: Name of the operation
    
    Yields:
        Dict with metrics
    """
    monitor = get_monitor()
    with monitor.measure(operation) as metrics:
        yield metrics


def get_system_info() -> Dict:
    """
    Get current system resource usage.
    
    Returns:
        Dict with system info
    """
    try:
        process = psutil.Process()
        
        return {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "num_threads": process.num_threads(),
            "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
        }
    except Exception as e:
        return {"error": str(e)}
