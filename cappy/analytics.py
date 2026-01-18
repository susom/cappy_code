"""Log analysis and usage statistics for Cappy Code."""

import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from collections import Counter, defaultdict


class LogAnalyzer:
    """Analyze Cappy Code JSONL logs for usage statistics."""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize log analyzer.
        
        Args:
            log_dir: Directory containing JSONL log files
        """
        self.log_dir = Path(log_dir)
    
    def load_logs(self, days: Optional[int] = None) -> List[dict]:
        """
        Load log entries from JSONL files.
        
        Args:
            days: Only load logs from last N days (None = all)
        
        Returns:
            List of log entry dicts
        """
        entries = []
        cutoff_date = None
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
        
        if not self.log_dir.exists():
            return entries
        
        for log_file in self.log_dir.glob("*.jsonl"):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            entry = json.loads(line)
                            
                            # Filter by date if specified
                            if cutoff_date and "timestamp" in entry:
                                entry_date = datetime.fromisoformat(entry["timestamp"])
                                if entry_date < cutoff_date:
                                    continue
                            
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
            except (OSError, IOError):
                continue
        
        return entries
    
    def tool_usage_stats(self, days: Optional[int] = None) -> Dict:
        """
        Get tool usage statistics.
        
        Args:
            days: Only analyze last N days
        
        Returns:
            Dict with tool usage stats
        """
        entries = self.load_logs(days=days)
        
        tool_counts = Counter()
        tool_durations = defaultdict(list)
        tool_errors = Counter()
        
        for entry in entries:
            if entry.get("type") != "tool_call":
                continue
            
            tool_name = entry.get("tool_name")
            if not tool_name:
                continue
            
            tool_counts[tool_name] += 1
            
            # Track duration
            if "duration_ms" in entry:
                tool_durations[tool_name].append(entry["duration_ms"])
            
            # Track errors
            if not entry.get("success", True):
                tool_errors[tool_name] += 1
        
        # Calculate averages
        avg_durations = {}
        for tool, durations in tool_durations.items():
            if durations:
                avg_durations[tool] = sum(durations) / len(durations)
        
        return {
            "total_calls": sum(tool_counts.values()),
            "by_tool": dict(tool_counts.most_common()),
            "avg_duration_ms": avg_durations,
            "errors_by_tool": dict(tool_errors),
            "period_days": days,
        }
    
    def session_stats(self, days: Optional[int] = None) -> Dict:
        """
        Get session statistics.
        
        Args:
            days: Only analyze last N days
        
        Returns:
            Dict with session stats
        """
        entries = self.load_logs(days=days)
        
        sessions = defaultdict(list)
        
        for entry in entries:
            session_id = entry.get("session_id", "unknown")
            sessions[session_id].append(entry)
        
        session_lengths = []
        session_tool_counts = []
        
        for session_id, session_entries in sessions.items():
            session_lengths.append(len(session_entries))
            
            tool_calls = sum(1 for e in session_entries if e.get("type") == "tool_call")
            session_tool_counts.append(tool_calls)
        
        return {
            "total_sessions": len(sessions),
            "avg_entries_per_session": sum(session_lengths) / len(session_lengths) if session_lengths else 0,
            "avg_tool_calls_per_session": sum(session_tool_counts) / len(session_tool_counts) if session_tool_counts else 0,
            "period_days": days,
        }
    
    def error_analysis(self, days: Optional[int] = None) -> Dict:
        """
        Analyze errors in logs.
        
        Args:
            days: Only analyze last N days
        
        Returns:
            Dict with error analysis
        """
        entries = self.load_logs(days=days)
        
        total_calls = 0
        errors = []
        error_types = Counter()
        
        for entry in entries:
            if entry.get("type") != "tool_call":
                continue
            
            total_calls += 1
            
            if not entry.get("success", True):
                errors.append(entry)
                
                # Try to categorize error
                result = entry.get("result", {})
                error_msg = result.get("error", "Unknown error")
                
                if "not found" in error_msg.lower():
                    error_types["not_found"] += 1
                elif "permission" in error_msg.lower():
                    error_types["permission"] += 1
                elif "timeout" in error_msg.lower():
                    error_types["timeout"] += 1
                else:
                    error_types["other"] += 1
        
        error_rate = len(errors) / total_calls if total_calls > 0 else 0
        
        return {
            "total_calls": total_calls,
            "total_errors": len(errors),
            "error_rate": error_rate,
            "error_types": dict(error_types),
            "recent_errors": errors[-10:],  # Last 10 errors
            "period_days": days,
        }
    
    def performance_summary(self, days: Optional[int] = None) -> Dict:
        """
        Get performance summary.
        
        Args:
            days: Only analyze last N days
        
        Returns:
            Dict with performance metrics
        """
        entries = self.load_logs(days=days)
        
        durations = []
        slow_calls = []
        
        for entry in entries:
            if entry.get("type") != "tool_call":
                continue
            
            duration = entry.get("duration_ms")
            if duration is not None:
                durations.append(duration)
                
                # Flag slow calls (> 5 seconds)
                if duration > 5000:
                    slow_calls.append({
                        "tool": entry.get("tool_name"),
                        "duration_ms": duration,
                        "timestamp": entry.get("timestamp"),
                    })
        
        if not durations:
            return {
                "avg_duration_ms": 0,
                "median_duration_ms": 0,
                "p95_duration_ms": 0,
                "slow_calls": [],
                "period_days": days,
            }
        
        durations.sort()
        n = len(durations)
        
        return {
            "avg_duration_ms": sum(durations) / n,
            "median_duration_ms": durations[n // 2],
            "p95_duration_ms": durations[int(n * 0.95)] if n > 0 else 0,
            "slow_calls": slow_calls[-10:],  # Last 10 slow calls
            "period_days": days,
        }
    
    def generate_report(self, days: Optional[int] = 7) -> str:
        """
        Generate a comprehensive usage report.
        
        Args:
            days: Analyze last N days (default: 7)
        
        Returns:
            Formatted report string
        """
        tool_stats = self.tool_usage_stats(days=days)
        session_stats = self.session_stats(days=days)
        error_stats = self.error_analysis(days=days)
        perf_stats = self.performance_summary(days=days)
        
        report = []
        report.append("=" * 60)
        report.append(f"Cappy Code Usage Report - Last {days} Days")
        report.append("=" * 60)
        report.append("")
        
        # Tool usage
        report.append("TOOL USAGE:")
        report.append(f"  Total tool calls: {tool_stats['total_calls']}")
        report.append("  By tool:")
        for tool, count in tool_stats['by_tool'].items():
            pct = (count / tool_stats['total_calls'] * 100) if tool_stats['total_calls'] > 0 else 0
            report.append(f"    {tool}: {count} ({pct:.1f}%)")
        report.append("")
        
        # Sessions
        report.append("SESSIONS:")
        report.append(f"  Total sessions: {session_stats['total_sessions']}")
        report.append(f"  Avg entries/session: {session_stats['avg_entries_per_session']:.1f}")
        report.append(f"  Avg tool calls/session: {session_stats['avg_tool_calls_per_session']:.1f}")
        report.append("")
        
        # Errors
        report.append("ERRORS:")
        report.append(f"  Total errors: {error_stats['total_errors']}")
        report.append(f"  Error rate: {error_stats['error_rate'] * 100:.2f}%")
        if error_stats['error_types']:
            report.append("  Error types:")
            for etype, count in error_stats['error_types'].items():
                report.append(f"    {etype}: {count}")
        report.append("")
        
        # Performance
        report.append("PERFORMANCE:")
        report.append(f"  Avg duration: {perf_stats['avg_duration_ms']:.0f}ms")
        report.append(f"  Median duration: {perf_stats['median_duration_ms']:.0f}ms")
        report.append(f"  P95 duration: {perf_stats['p95_duration_ms']:.0f}ms")
        report.append(f"  Slow calls (>5s): {len(perf_stats['slow_calls'])}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def analyze_logs(log_dir: str = "./logs", days: int = 7) -> str:
    """
    Convenience function to analyze logs and generate report.
    
    Args:
        log_dir: Directory containing logs
        days: Number of days to analyze
    
    Returns:
        Formatted report string
    """
    analyzer = LogAnalyzer(log_dir=log_dir)
    return analyzer.generate_report(days=days)
