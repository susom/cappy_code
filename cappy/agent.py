"""Agentic loop orchestrator for Cappy Code."""

import json
import re
from pathlib import Path
from typing import Optional, Union

from cappy import tools
from cappy.ai_client import chat_completion, AGENTIC_MODELS, DEFAULT_MODEL
from cappy.config import get_config
from cappy.logger import log_action

# Safety limits
MAX_ITERATIONS = 20
MAX_TOOL_CALLS = 50

# JSON Schema for structured agent responses with COMPLETE tool_args definition
# Azure OpenAI strict mode requires all properties to be defined when additionalProperties=false
AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "thinking": {
            "type": "string",
            "description": "Your reasoning about what to do next"
        },
        "action": {
            "type": "string",
            "enum": ["tool_call", "done"],
            "description": "Either 'tool_call' to use a tool, or 'done' when task is complete"
        },
        "tool_name": {
            "type": "string",
            "enum": ["scan", "search", "read", "write", "edit", "apply", "run", "delete", "move", "copy"],
            "description": "Which tool to use (required if action=tool_call)"
        },
        "tool_args": {
            "type": "object",
            "description": "Arguments for the tool (required if action=tool_call). Use only the properties needed for the specific tool.",
            "properties": {
                # scan tool
                "path": {
                    "type": "string",
                    "description": "File or directory path (for scan, search, read, write)"
                },
                # search tool
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for (for search tool)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results (for search tool)"
                },
                # read tool
                "start": {
                    "type": "integer",
                    "description": "Starting line number (for read tool)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (for read tool)"
                },
                # write tool
                "content": {
                    "type": "string",
                    "description": "File content to write (for write tool)"
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Allow overwriting existing file (for write, move, copy tools)"
                },
                # edit tool
                "filepath": {
                    "type": "string",
                    "description": "File path (for edit, delete tools)"
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact string to find and replace (for edit tool)"
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement string (for edit tool)"
                },
                # apply tool
                "patch_path": {
                    "type": "string",
                    "description": "Path to patch file (for apply tool)"
                },
                # run tool
                "command": {
                    "type": "string",
                    "description": "Shell command to execute (for run tool)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (for run tool)"
                },
                # delete tool
                "confirm": {
                    "type": "boolean",
                    "description": "Confirmation required for destructive operations (for delete tool)"
                },
                # move and copy tools
                "src": {
                    "type": "string",
                    "description": "Source path (for move, copy tools)"
                },
                "dst": {
                    "type": "string",
                    "description": "Destination path (for move, copy tools)"
                }
            },
            "required": ["path", "pattern", "max_results", "start", "limit", "content", "overwrite", "filepath", "old_string", "new_string", "patch_path", "command", "timeout", "confirm", "src", "dst"],  # Azure strict mode requires ALL properties in required array
            "additionalProperties": False  # Required by Azure OpenAI strict mode
        },
        "message": {
            "type": "string",
            "description": "Message to user - brief explanation of what you're doing, or final answer if action=done"
        }
    },
    "required": ["thinking", "action", "tool_name", "tool_args", "message"],
    "additionalProperties": False
}

BASE_SYSTEM_PROMPT = """You are Cappy, a PHI-safe code assistant. You help users with code tasks by using tools.

## Available Tools

1. **scan** - Scan repository structure
   Args: {"path": "." }
   Returns: file count, directory count, extension breakdown, file tree

2. **search** - Search for pattern in file contents
   Args: {"pattern": "regex_pattern", "path": ".", "max_results": 50}
   Returns: matching lines with file paths and line numbers

3. **read** - Read file contents
   Args: {"path": "file_path", "start": 1, "limit": null}
   Returns: file contents with line numbers

4. **apply** - Apply a unified diff patch (you must create the patch file first)
   Args: {"patch_path": "path/to/patch.diff"}
   Returns: success/failure, files touched

5. **run** - Execute a shell command
   Args: {"command": "shell command here", "timeout": 60}
   Returns: exit_code, stdout, stderr

6. **write** - Create or overwrite a file
   Args: {"path": "file_path", "content": "file contents here", "overwrite": false}
   Returns: success/failure, bytes written
   Note: Creates parent directories automatically. Set overwrite=true to replace existing files.

7. **edit** - Perform surgical edit on existing file (PREFERRED for editing files)
   Args: {"filepath": "file_path", "old_string": "exact text to replace", "new_string": "replacement text"}
   Returns: success/failure
   Note: old_string must be unique in the file. If it appears multiple times, provide more context to make it unique.

8. **delete** - Delete a file or directory
   Args: {"filepath": "path/to/file", "confirm": true}
   Returns: success/failure
   Note: Requires confirm=true. Use with caution - deletion is permanent.

9. **move** - Move or rename a file or directory
   Args: {"src": "old/path", "dst": "new/path", "overwrite": false}
   Returns: success/failure, src, dst

10. **copy** - Copy a file or directory
   Args: {"src": "source/path", "dst": "dest/path", "overwrite": false}
   Returns: success/failure, src, dst, bytes_copied

## How to respond

Your response MUST be valid JSON matching this structure:
{
  "thinking": "Brief reasoning about what to do next",
  "action": "tool_call" or "done",
  "tool_name": "scan|search|read|write|apply|run|delete|move|copy" (required if action=tool_call),
  "tool_args": {...} (required if action=tool_call, MUST be an object with the appropriate properties for the tool),
  "message": "Brief explanation of what you're doing, or final answer if done"
}

Examples:
{"thinking": "Need to understand repo structure", "action": "tool_call", "tool_name": "scan", "tool_args": {"path": ".", "pattern": "", "max_results": 0, "start": 0, "limit": 0, "content": "", "overwrite": false, "filepath": "", "old_string": "", "new_string": "", "patch_path": "", "command": "", "timeout": 0, "confirm": false, "src": "", "dst": ""}, "message": "Scanning repository structure"}
{"thinking": "User wants to read agent.py", "action": "tool_call", "tool_name": "read", "tool_args": {"path": "cappy/agent.py", "pattern": "", "max_results": 0, "start": 1, "limit": 0, "content": "", "overwrite": false, "filepath": "", "old_string": "", "new_string": "", "patch_path": "", "command": "", "timeout": 0, "confirm": false, "src": "", "dst": ""}, "message": "Reading cappy/agent.py"}
{"thinking": "Found the bug, task complete", "action": "done", "tool_name": "scan", "tool_args": {"path": "", "pattern": "", "max_results": 0, "start": 0, "limit": 0, "content": "", "overwrite": false, "filepath": "", "old_string": "", "new_string": "", "patch_path": "", "command": "", "timeout": 0, "confirm": false, "src": "", "dst": ""}, "message": "Fixed the authentication bug in auth.py:42"}

## Rules
- **BE AUTONOMOUS. DO NOT ASK PERMISSION. Just do the task.**
- Only ask for confirmation before: deleting files, running destructive commands, or system-level operations
- For reading files, searching, writing code - JUST DO IT. Don't ask "would you like me to...?"
- Use tools to gather information before making changes
- **IMPORTANT: NEVER use run with cat/echo/heredoc to create or edit files.**
- For NEW files: use write tool with the full file content
- For EDITING existing files: use edit tool (read the file first, then use edit with old_string/new_string)
- The edit tool is MUCH more reliable than write for edits - it prevents mistakes
- One tool call at a time
- Briefly explain what you're doing in the "message" field, then DO IT
- If something fails, explain the error and fix it or suggest alternatives
- **CRITICAL: tool_args MUST always include ALL 16 properties (path, pattern, max_results, start, limit, content, overwrite, filepath, old_string, new_string, patch_path, command, timeout, confirm, src, dst). Use empty strings "" for unused string properties, 0 for unused numbers, false for unused booleans.**
- **IMPORTANT: When using read tool, set "path" to the file path and leave other properties as empty defaults**
"""


def load_project_context(cwd: Optional[str] = None) -> Optional[str]:
    """
    Load CAPPY.md from current working directory if it exists.

    Returns the file content, or None if not found.
    """
    work_dir = Path(cwd) if cwd else Path.cwd()
    cappy_md = work_dir / "CAPPY.md"

    if cappy_md.exists():
        try:
            return cappy_md.read_text(encoding="utf-8")
        except (OSError, IOError):
            return None
    return None


def get_system_prompt(cwd: Optional[str] = None) -> str:
    """
    Build full system prompt, including CAPPY.md context if present.
    """
    project_context = load_project_context(cwd)

    if project_context:
        return f"""{BASE_SYSTEM_PROMPT}

## Project Context (from CAPPY.md)

{project_context}
"""
    return BASE_SYSTEM_PROMPT


# Legacy alias
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def normalize_tool_args(args: Union[dict, list, None]) -> dict:
    """
    Normalize tool_args to always be a dict.
    
    SecureChatAI with json_schema sometimes returns:
    - Empty list [] instead of empty object {}
    - None instead of {}
    
    This function ensures we always get a dict for safe .get() calls.
    """
    if args is None:
        return {}
    if isinstance(args, list):
        # Empty list from AI -> empty dict
        return {}
    if isinstance(args, dict):
        return args
    # Fallback for any other type
    return {}


def parse_agent_response(response: Union[str, dict]) -> Optional[dict]:
    """
    Parse the AI's structured JSON response.
    
    Handles both string and dict inputs:
    - When json_schema is used, SecureChatAI returns parsed dict directly
    - Without json_schema, it returns a JSON string
    
    Returns dict with parsed response data, or None if invalid.
    Expected format:
    {
      "thinking": "...",
      "action": "tool_call" | "done",
      "tool_name": "..." (if tool_call),
      "tool_args": {...} (if tool_call),
      "message": "..."
    }
    """
    try:
        # Handle both string and dict responses
        if isinstance(response, dict):
            data = response
        else:
            # Try to parse as JSON string
            data = json.loads(response)

        # Validate required fields
        if "action" not in data or "message" not in data:
            return None

        if data["action"] == "tool_call":
            if "tool_name" not in data or "tool_args" not in data:
                return None
            
            # Normalize tool_args to dict (handles [] from AI)
            data["tool_args"] = normalize_tool_args(data["tool_args"])

        return data

    except (json.JSONDecodeError, TypeError):
        # Fallback: try to extract JSON from markdown code blocks
        if isinstance(response, str):
            match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if "action" in data and "message" in data:
                        # Normalize tool_args here too
                        if "tool_args" in data:
                            data["tool_args"] = normalize_tool_args(data["tool_args"])
                        return data
                except json.JSONDecodeError:
                    pass

        return None


def execute_tool(name: str, args: Union[dict, list, None]) -> dict:
    """
    Execute a tool by name with given args.
    
    Args are normalized to dict to handle edge cases from SecureChatAI.
    """
    # Normalize args to dict (handles [], None, etc.)
    args = normalize_tool_args(args)

    if name == "scan":
        return tools.scan(args.get("path", "."))

    elif name == "search":
        return tools.search(
            args.get("pattern", ""),
            args.get("path", "."),
            max_results=args.get("max_results", 50)
        )

    elif name == "read":
        return tools.read(
            args.get("path", ""),
            start=args.get("start", 1),
            limit=args.get("limit")
        )

    elif name == "apply":
        config = get_config()
        max_files = config.get("max_files_touched_per_run", 5)
        return tools.apply(args.get("patch_path", ""), max_files=max_files)

    elif name == "run":
        return tools.run(
            args.get("command", ""),
            timeout=args.get("timeout", 60)
        )

    elif name == "write":
        return tools.write(
            args.get("path", ""),
            args.get("content", ""),
            overwrite=args.get("overwrite", False)
        )

    elif name == "edit":
        return tools.edit(
            args.get("filepath", ""),
            args.get("old_string", ""),
            args.get("new_string", "")
        )

    elif name == "delete":
        return tools.delete(
            args.get("filepath", ""),
            confirm=args.get("confirm", False)
        )

    elif name == "move":
        return tools.move(
            args.get("src", ""),
            args.get("dst", ""),
            overwrite=args.get("overwrite", False)
        )

    elif name == "copy":
        return tools.copy(
            args.get("src", ""),
            args.get("dst", ""),
            overwrite=args.get("overwrite", False)
        )

    else:
        return {"error": f"Unknown tool: {name}"}


def run_agent(
    task: str,
    model: Optional[str] = None,
    max_iterations: int = MAX_ITERATIONS,
    verbose: bool = True,
) -> dict:
    """
    Run the agentic loop for a given task.

    Args:
        task: The user's task/request
        model: Model to use (default from config)
        max_iterations: Max loop iterations (safety limit)
        verbose: Print progress to stdout

    Returns:
        dict with:
            - success: bool
            - result: str (final answer or error)
            - iterations: int
            - tool_calls: list of tool calls made
    """
    config = get_config()
    resolved_model = model or config.get("default_model", DEFAULT_MODEL)

    if resolved_model not in AGENTIC_MODELS:
        return {
            "success": False,
            "result": f"Model {resolved_model} not in AGENTIC_MODELS: {AGENTIC_MODELS}",
            "iterations": 0,
            "tool_calls": [],
        }

    # Build conversation history
    messages = []
    messages.append(f"USER TASK: {task}")

    tool_calls_made = []
    iteration = 0

    if verbose:
        print(f"[agent] Starting task with model={resolved_model}")
        print(f"[agent] Task: {task}\n")

    while iteration < max_iterations:
        iteration += 1

        if verbose:
            print(f"[agent] Iteration {iteration}/{max_iterations}")

        # Build prompt with history
        conversation = "\n\n".join(messages)

        # Call AI with JSON schema enforcement
        response = chat_completion(
            prompt=conversation,
            model=resolved_model,
            system_prompt=get_system_prompt(),
            json_schema=AGENT_RESPONSE_SCHEMA,
            max_tokens=32000,
            temperature=0.2,
        )

        if not response["success"]:
            return {
                "success": False,
                "result": f"AI call failed: {response.get('error', 'Unknown error')}",
                "iterations": iteration,
                "tool_calls": tool_calls_made,
            }

        ai_response = response["content"]
        
        # Convert dict to string for message history (if needed)
        if isinstance(ai_response, dict):
            ai_response_str = json.dumps(ai_response)
        else:
            ai_response_str = ai_response
            
        messages.append(f"ASSISTANT: {ai_response_str}")

        if verbose:
            # Print truncated response
            display = ai_response_str[:500] + "..." if len(ai_response_str) > 500 else ai_response_str
            print(f"[ai] {display}\n")

        # Parse structured response (handles both dict and string)
        parsed = parse_agent_response(ai_response)
        if not parsed:
            # Invalid response format - nudge the AI
            messages.append("SYSTEM: Invalid response format. Please respond with valid JSON matching the schema.")
            continue

        # Show thinking and message if verbose
        if verbose and "thinking" in parsed:
            print(f"[thinking] {parsed['thinking']}")
        if verbose and "message" in parsed:
            print(f"[message] {parsed['message']}\n")

        # Check if done
        if parsed["action"] == "done":
            if verbose:
                print(f"[agent] Task complete.\n")

            log_action("agent_run", {"task": task, "model": resolved_model},
                      {"iterations": iteration, "tool_calls": len(tool_calls_made)},
                      success=True)

            return {
                "success": True,
                "result": parsed["message"],
                "iterations": iteration,
                "tool_calls": tool_calls_made,
            }

        # Handle tool call
        if parsed["action"] == "tool_call":
            tool_name = parsed["tool_name"]
            tool_args = parsed["tool_args"]

            if verbose:
                print(f"[tool] {tool_name}({json.dumps(tool_args)})")

            # Safety check
            if len(tool_calls_made) >= MAX_TOOL_CALLS:
                return {
                    "success": False,
                    "result": f"Exceeded max tool calls ({MAX_TOOL_CALLS})",
                    "iterations": iteration,
                    "tool_calls": tool_calls_made,
                }

            # Execute tool (with normalized args)
            tool_result = execute_tool(tool_name, tool_args)
            tool_calls_made.append({
                "name": tool_name,
                "args": tool_args,
                "result_summary": str(tool_result)[:200],
            })

            if verbose:
                result_display = json.dumps(tool_result, indent=2)
                if len(result_display) > 500:
                    result_display = result_display[:500] + "..."
                print(f"[result] {result_display}\n")

            # Add result to conversation
            messages.append(f"TOOL RESULT ({tool_name}): {json.dumps(tool_result)}")

    # Hit max iterations
    log_action("agent_run", {"task": task, "model": resolved_model},
              {"iterations": iteration, "tool_calls": len(tool_calls_made), "error": "max_iterations"},
              success=False)

    return {
        "success": False,
        "result": f"Reached max iterations ({max_iterations}) without completing task",
        "iterations": iteration,
        "tool_calls": tool_calls_made,
    }
