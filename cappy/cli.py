#!/usr/bin/env python3
"""Cappy Code CLI - PHI-safe agentic code runner."""

import argparse
import json
import sys
import time

from cappy import __version__
from cappy import tools
from cappy.agent import run_agent
from cappy.chat import run_chat
from cappy.config import get_config, validate_config
from cappy.analytics import analyze_logs
from cappy.logger import log_action


def cmd_scan(args):
    """Handle scan command."""
    inputs = {"path": args.path}
    start = time.perf_counter()
    result = tools.scan(args.path)
    duration_ms = (time.perf_counter() - start) * 1000
    success = "error" not in result
    log_action("scan", inputs, result, success, duration_ms)
    print(json.dumps(result, indent=2))
    return 0 if success else 1


def cmd_search(args):
    """Handle search command."""
    inputs = {"pattern": args.pattern, "path": args.path, "max": args.max}
    start = time.perf_counter()
    result = tools.search(args.pattern, args.path, max_results=args.max)
    duration_ms = (time.perf_counter() - start) * 1000
    success = "error" not in result
    log_action("search", inputs, result, success, duration_ms)
    print(json.dumps(result, indent=2))
    return 0 if success else 1


def cmd_read(args):
    """Handle read command."""
    inputs = {"path": args.path, "start": args.start, "limit": args.limit}
    start = time.perf_counter()
    result = tools.read(args.path, start=args.start, limit=args.limit)
    duration_ms = (time.perf_counter() - start) * 1000
    success = "error" not in result
    log_action("read", inputs, result, success, duration_ms)

    if not success:
        print(json.dumps(result, indent=2))
        return 1

    # Print content directly for readability, metadata as JSON header
    meta = {k: v for k, v in result.items() if k != "content"}
    print(f"# {json.dumps(meta)}")
    print(result["content"])
    return 0


def cmd_apply(args):
    """Handle apply command."""
    config = get_config()
    # Use CLI arg if provided, otherwise use config
    max_files = args.max_files if args.max_files is not None else config["max_files_touched_per_run"]
    inputs = {"patch": args.patch, "max_files": max_files}
    start = time.perf_counter()
    result = tools.apply(args.patch, max_files=max_files)
    duration_ms = (time.perf_counter() - start) * 1000
    success = result.get("success", False)
    log_action("apply", inputs, result, success, duration_ms)
    print(json.dumps(result, indent=2))
    return 0 if success else 1


def cmd_run(args):
    """Handle run command."""
    inputs = {"command": args.command, "timeout": args.timeout}
    start = time.perf_counter()
    result = tools.run(args.command, timeout=args.timeout)
    duration_ms = (time.perf_counter() - start) * 1000
    success = result.get("exit_code", 1) == 0
    log_action("run", inputs, result, success, duration_ms)
    print(json.dumps(result, indent=2))
    return result.get("exit_code", 1)


def cmd_agent(args):
    """Handle agent command - run agentic loop."""
    result = run_agent(
        task=args.task,
        model=args.model,
        max_iterations=args.max_iterations,
        verbose=not args.quiet,
    )

    if not args.quiet:
        print("\n" + "=" * 50)
        print("FINAL RESULT:")
        print("=" * 50)

    print(result["result"])

    if not args.quiet:
        print(f"\n[{result['iterations']} iterations, {len(result['tool_calls'])} tool calls]")

    return 0 if result["success"] else 1


def cmd_chat(args):
    """Handle chat command - interactive chat loop."""
    run_chat(model=args.model)
    return 0


def cmd_config_validate(args):
    """Handle config validate command."""
    is_valid, errors = validate_config(args.config)
    
    if is_valid:
        print("✅ Configuration is valid")
        return 0
    else:
        print("❌ Configuration has errors:")
        for error in errors:
            print(f"  - {error}")
        return 1


def cmd_analytics(args):
    """Handle analytics command."""
    config = get_config()
    log_dir = config.get("log_dir", "./logs")
    
    report = analyze_logs(log_dir=log_dir, days=args.days)
    print(report)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="cappy",
        description="PHI-safe agentic code runner CLI",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan repository and print summary")
    p_scan.add_argument("path", nargs="?", default=".", help="Root path to scan")
    p_scan.set_defaults(func=cmd_scan)

    # search
    p_search = subparsers.add_parser("search", help="Search for pattern in files")
    p_search.add_argument("pattern", help="Regex pattern to search")
    p_search.add_argument("path", nargs="?", default=".", help="Path to search in")
    p_search.add_argument("--max", type=int, default=50, help="Max results")
    p_search.set_defaults(func=cmd_search)

    # read
    p_read = subparsers.add_parser("read", help="Read file contents")
    p_read.add_argument("path", help="File path to read")
    p_read.add_argument("--start", type=int, default=1, help="Start line (1-indexed)")
    p_read.add_argument("--limit", type=int, default=None, help="Max lines to read")
    p_read.set_defaults(func=cmd_read)

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply unified diff patch")
    p_apply.add_argument("patch", help="Path to patch file (.diff)")
    p_apply.add_argument(
        "--max-files", type=int, default=None,
        help="Max files allowed in patch (default from config)"
    )
    p_apply.set_defaults(func=cmd_apply)

    # run
    p_run = subparsers.add_parser("run", help="Run shell command")
    p_run.add_argument("command", help="Command to execute")
    p_run.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    p_run.set_defaults(func=cmd_run)

    # agent
    p_agent = subparsers.add_parser("agent", help="Run agentic loop for a task")
    p_agent.add_argument("task", help="Task description for the agent")
    p_agent.add_argument("--model", default=None, help="Model to use (default from config)")
    p_agent.add_argument("--max-iterations", type=int, default=20, help="Max loop iterations")
    p_agent.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    p_agent.set_defaults(func=cmd_agent)

    # chat
    p_chat = subparsers.add_parser("chat", help="Interactive chat with tools")
    p_chat.add_argument("--model", default=None, help="Model to use (default from config)")
    p_chat.set_defaults(func=cmd_chat)

    # config
    p_config = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = p_config.add_subparsers(dest="config_command", required=True)
    
    p_config_validate = config_subparsers.add_parser("validate", help="Validate configuration file")
    p_config_validate.add_argument("--config", default=None, help="Path to config file")
    p_config_validate.set_defaults(func=cmd_config_validate)

    # analytics
    p_analytics = subparsers.add_parser("analytics", help="Analyze usage logs and statistics")
    p_analytics.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    p_analytics.set_defaults(func=cmd_analytics)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
