"""Interactive chat interface for Cappy Code."""

import json
import readline  # enables arrow keys, history in input()
from typing import Optional

from cappy import __version__
from cappy.agent import (
    get_system_prompt,
    parse_agent_response,
    execute_tool,
    MAX_TOOL_CALLS,
    AGENT_RESPONSE_SCHEMA,
)
from cappy.ai_client import chat_completion, AGENTIC_MODELS, DEFAULT_MODEL
from cappy.config import get_config


WELCOME = f"""
╔═══════════════════════════════════════════════════════════╗
║  Cappy Code v{__version__:<44} ║
║  PHI-safe agentic code runner                             ║
╠═══════════════════════════════════════════════════════════╣
║  Commands:                                                ║
║    /help     - Show this help                             ║
║    /paste    - Multi-line input mode (end with EOF)       ║
║    /clear    - Clear conversation history                 ║
║    /model    - Show/change model                          ║
║    /quit     - Exit chat                                  ║
╚═══════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Available commands:
  /help          Show this help message
  /paste         Enter multi-line input mode (paste text, then type EOF on its own line)
  /clear         Clear conversation history and start fresh
  /model         Show current model
  /model <name>  Switch to a different model
  /history       Show conversation history length
  /quit or /q    Exit the chat

Tips:
- Ask questions about code, request file searches, or give tasks
- The AI can use tools: scan, search, read, apply, run, write
- Tool calls happen automatically when needed
- Use /paste to paste multi-line error messages or code blocks
- Ctrl+C to interrupt, Ctrl+D to exit
"""


def run_chat(model: Optional[str] = None):
    """
    Run interactive chat loop.

    Args:
        model: Initial model to use (default from config)
    """
    config = get_config()
    current_model = model or config.get("default_model", DEFAULT_MODEL)

    print(WELCOME)
    print(f"  Model: {current_model}")
    print(f"  Type /help for commands\n")

    # Conversation history
    messages = []
    tool_calls_this_session = 0

    while True:
        try:
            user_input = input("\n\033[1;32myou>\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            cmd_result = handle_command(user_input, messages, current_model)
            if cmd_result == "quit":
                print("Goodbye!")
                break
            elif cmd_result == "clear":
                messages = []
                tool_calls_this_session = 0
                print("Conversation cleared.")
                continue
            elif cmd_result.startswith("model:"):
                new_model = cmd_result.split(":", 1)[1]
                if new_model in AGENTIC_MODELS:
                    current_model = new_model
                    print(f"Switched to model: {current_model}")
                else:
                    print(f"Unknown model: {new_model}")
                    print(f"Available: {', '.join(AGENTIC_MODELS)}")
                continue
            elif cmd_result == "paste":
                print("Paste mode: Enter text, then type EOF on its own line to submit.")
                print("-" * 40)
                lines = []
                while True:
                    try:
                        line = input()
                        if line.strip().upper() in ("EOF", "---"):
                            break
                        lines.append(line)
                    except EOFError:
                        break
                if lines:
                    user_input = "\n".join(lines)
                    print("-" * 40)
                    print(f"[Captured {len(lines)} lines]")
                else:
                    print("No input captured.")
                    continue
                # Fall through to process the pasted input
            elif cmd_result:
                print(cmd_result)
                continue

        # Add user message to history
        messages.append(f"USER: {user_input}")

        # Process with potential tool calls
        tool_calls_this_turn = 0
        max_tool_calls_per_turn = 10

        while tool_calls_this_turn < max_tool_calls_per_turn:
            # Build conversation for AI
            conversation = "\n\n".join(messages)

            # Call AI
            print("\n\033[1;31mcappy>\033[0m ", end="", flush=True)

            response = chat_completion(
                prompt=conversation,
                model=current_model,
                system_prompt=get_system_prompt(),
                json_schema=AGENT_RESPONSE_SCHEMA,
                max_tokens=4096,
                temperature=0.2,
            )

            if not response["success"]:
                print(f"\n[Error: {response.get('error', 'Unknown error')}]")
                break

            ai_response = response["content"]

            # Parse structured response
            parsed = parse_agent_response(ai_response)

            if not parsed:
                # Invalid format - show raw response and break
                print(f"\n[Invalid response format]")
                print(ai_response)
                messages.append(f"ASSISTANT: {ai_response}")
                break

            # Check for tool call
            if parsed["action"] == "tool_call":
                tool_name = parsed["tool_name"]
                tool_args = parsed["tool_args"]

                # Show the message from AI
                if parsed.get("message"):
                    print(parsed["message"])

                print(f"\n\033[1;33m[tool: {tool_name}]\033[0m", end=" ")

                # Execute tool
                tool_result = execute_tool(tool_name, tool_args)
                tool_calls_this_turn += 1
                tool_calls_this_session += 1

                # Show brief result
                if "error" in tool_result:
                    print(f"\033[1;31m{tool_result['error']}\033[0m")
                else:
                    # Show truncated success indicator
                    result_str = json.dumps(tool_result)
                    if len(result_str) > 100:
                        print(f"OK ({len(result_str)} chars)")
                    else:
                        print("OK")

                # Add to conversation
                messages.append(f"ASSISTANT: {ai_response}")
                messages.append(f"TOOL RESULT ({tool_name}): {json.dumps(tool_result)}")

                # Safety check
                if tool_calls_this_session >= MAX_TOOL_CALLS:
                    print("\n[Max tool calls reached for session. Use /clear to reset.]")
                    break

                # Continue loop to let AI respond to tool result
                continue

            else:
                # Action is "done" - just show the message
                print(parsed["message"])
                messages.append(f"ASSISTANT: {ai_response}")

                # Done with this turn
                break


def handle_command(cmd: str, messages: list, current_model: str) -> str:
    """Handle slash commands. Returns action or message to display."""
    cmd_lower = cmd.lower().strip()

    if cmd_lower in ("/quit", "/q", "/exit"):
        return "quit"

    elif cmd_lower == "/clear":
        return "clear"

    elif cmd_lower == "/help":
        return HELP_TEXT

    elif cmd_lower == "/paste":
        return "paste"

    elif cmd_lower == "/history":
        return f"Conversation has {len(messages)} messages."

    elif cmd_lower == "/model":
        return f"Current model: {current_model}\nAvailable: {', '.join(AGENTIC_MODELS)}"

    elif cmd_lower.startswith("/model "):
        new_model = cmd[7:].strip()
        return f"model:{new_model}"

    else:
        return f"Unknown command: {cmd}\nType /help for available commands."
