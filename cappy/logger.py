"""Structured JSON lines logging for audit trail, plus optional human-friendly lines."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

class RunLogger:
    """
    Logs tool invocations to JSON lines files in ./logs/.

    Each run creates entries in: logs/cappy_YYYY-MM-DD.jsonl
    Optionally, prints a friendly text line as well.
    """

    def __init__(self, log_dir: str = "./logs", human_friendly: bool = True):
        self.log_dir = Path(log_dir)
        self.human_friendly = human_friendly
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        """Get today's log file path."""
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return self.log_dir / f"cappy_{date_str}.jsonl"

    def log(
        self,
        action: str,
        inputs: dict[str, Any],
        output: dict[str, Any],
        success: bool,
        duration_ms: Optional[float] = None,
    ):
        """
        Log a tool or AI call.

        Args:
            action: Tool or action name (e.g. 'scan', 'search', 'ai_chat')
            inputs: Input arguments
            output: Output result
            success: Whether the action succeeded
            duration_ms: Execution time in milliseconds
        """
        # Create the JSON entry
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "inputs": self._sanitize(inputs),
            "output": self._truncate_output(output),
            "success": success,
        }
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        # Write JSON lines entry
        log_file = self._get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Optionally, also append a simpler "human-friendly" line
        if self.human_friendly:
            friendly_line = self._format_friendly_line(entry)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"# {friendly_line}\n")

    def _format_friendly_line(self, entry: dict[str, Any]) -> str:
        """
        Produce a simple text line summarizing the entry for quick reading.
        """
        ts = entry.get("ts", "").replace("T", " ")[:19]
        action = entry.get("action", "?")
        success = "SUCCESS" if entry.get("success") else "FAIL"
        inputs = entry.get("inputs", {})
        output = entry.get("output", {})
        # Summarize inputs and output in short form
        in_short = ", ".join(f"{k}={v}" for k,v in inputs.items() if v is not None)
        out_short = ", ".join(f"{k}={v}" for k,v in output.items() if v is not None)
        return f"[{ts}] {action} {success} | Inputs: {in_short} | Output: {out_short}"

    def _sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive info from inputs, but not max_tokens or max_completion_tokens."""
        sanitized = {}
        # We remove 'token' from the set so we don’t collide with max_tokens.
        sensitive_keys = {"password", "secret", "credential", "api_key"}  # removed 'token'

        for k, v in data.items():
            lowercase_key = k.lower()
            # If the key is exactly 'max_tokens' or 'max_completion_tokens', skip.
            if lowercase_key in ["max_tokens", "max_completion_tokens"]:
                sanitized[k] = v
            # Else, check if it matches the sensitive keys.
            elif any(s in lowercase_key for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 500:
                sanitized[k] = v[:500] + "...[truncated]"
            else:
                sanitized[k] = v

        return sanitized

    def _truncate_output(self, output: dict[str, Any], max_len: int = 2000) -> dict[str, Any]:
        """Truncate large output fields for logging."""
        truncated = {}
        for k, v in output.items():
            if isinstance(v, str) and len(v) > max_len:
                truncated[k] = v[:max_len] + f"...[truncated, total {len(v)} chars]"
            elif isinstance(v, list) and len(v) > 20:
                truncated[k] = v[:20]
                truncated[f"{k}_truncated"] = True
                truncated[f"{k}_total"] = len(v)
            else:
                truncated[k] = v
        return truncated

# Global logger instance
_logger: Optional[RunLogger] = None

def get_logger(log_dir: str = "./logs", human_friendly: bool = True) -> RunLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = RunLogger(log_dir, human_friendly=human_friendly)
    return _logger

def log_action(
    action: str,
    inputs: dict[str, Any],
    output: dict[str, Any],
    success: bool,
    duration_ms: Optional[float] = None,
):
    """Convenience function to log an action."""
    get_logger().log(action, inputs, output, success, duration_ms)
