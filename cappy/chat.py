"""Interactive chat interface for Cappy Code."""

import json
import readline  # enables arrow keys, history in input()
from pathlib import Path
from typing import Optional
from datetime import datetime

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
║    /help       - Show this help                           ║
║    /save       - Save conversation                        ║
║    /load       - Load conversation                        ║
║    /undo       - Undo last file change                    ║
║    /clear      - Clear conversation history               ║
║    /quit       - Exit chat                                ║
╚═══════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Available commands:
  /help          Show this help message
  /save          Save conversation (auto-generates filename)
  /save <name>   Save conversation with specific filename
  /load          List available saved conversations
  /load <name>   Load a saved conversation
  /paste         Enter multi-line input mode (paste text, then type EOF on its own line)
  /clear         Clear conversation history and start fresh
  /model         Show current model
  /model <name>  Switch to a different model
  /history       Show conversation history length
  /undo          Undo last file change (pops git stash)
  /snapshots     List available undo snapshots
  /quit or /q    Exit the chat

Tips:
- Ask questions about code, request file searches, or give tasks
- The AI can use tools: scan, search, read, write, edit, apply, run, delete, move, copy
- Tool calls happen automatically when needed
- Automatic snapshots are created before destructive operations (write, edit, delete)
- Use /undo to revert changes, /snapshots to see what's available
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
            elif cmd_result == "save":
                # Auto-generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_{timestamp}.json"
                save_conversation(messages, filename)
                print(f"Conversation saved to {filename}")
                continue
            elif cmd_result.startswith("save:"):
                filename = cmd_result.split(":", 1)[1]
                if not filename.endswith(".json"):
                    filename += ".json"
                save_conversation(messages, filename)
                print(f"Conversation saved to {filename}")
                continue
            elif cmd_result == "load":
                # List available conversations
                conversations = list_conversations()
                if not conversations:
                    print("No saved conversations found.")
                else:
                    print("Available conversations:")
                    for conv in conversations:
                        print(f"  {conv}")
                    print("Use /load <filename> to load one.")
                continue
            elif cmd_result.startswith("load:"):
                filename = cmd_result.split(":", 1)[1]
                if not filename.endswith(".json"):
                    filename += ".json"
                loaded_messages = load_conversation(filename)
                if loaded_messages is not None:
                    messages = loaded_messages
                    print(f"Loaded {len(messages)} messages from {filename}")
                else:
                    print(f"Failed to load {filename}")
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
                else:
                    print("No input received.")
                    continue
            else:
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
                # Invalid format - nudge the AI to use correct format
                print(f"\n[Invalid response format - asking AI to reformat...]")
                messages.append(f"ASSISTANT: {ai_response}")
                messages.append("SYSTEM: Invalid response format. Please respond with valid JSON matching the schema: {\"action\": \"done\", \"message\": \"your message here\"}")
                # Continue loop to let AI retry with correct format
                continue

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

    elif cmd_lower == "/undo":
        try:
            from cappy.undo import get_undo_manager
            undo_mgr = get_undo_manager()
            success, msg = undo_mgr.undo()
            return msg
        except Exception as e:
            return f"Undo failed: {e}"

    elif cmd_lower == "/snapshots":
        try:
            from cappy.undo import get_undo_manager
            undo_mgr = get_undo_manager()
            snapshots = undo_mgr.list_snapshots()
            if not snapshots:
                return "No snapshots available."
            result = "Available snapshots:\n"
            for snap in snapshots:
                result += f"  {snap['ref']}: {snap['message']}\n"
            return result
        except Exception as e:
            return f"Failed to list snapshots: {e}"

    elif cmd_lower == "/save":
        return "save"

    elif cmd_lower.startswith("/save "):
        filename = cmd[6:].strip()
        return f"save:{filename}"

    elif cmd_lower == "/load":
        return "load"

    elif cmd_lower.startswith("/load "):
        filename = cmd[6:].strip()
        return f"load:{filename}"

    else:
        return f"Unknown command: {cmd}\nType /help for available commands."


def save_conversation(messages: list, filename: str) -> bool:
    """Save conversation to JSON file."""
    try:
        save_dir = Path("./conversations")
        save_dir.mkdir(exist_ok=True)
        
        filepath = save_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "messages": messages,
            }, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False


def load_conversation(filename: str) -> Optional[list]:
    """Load conversation from JSON file."""
    try:
        save_dir = Path("./conversations")
        filepath = save_dir / filename
        
        if not filepath.exists():
            print(f"File not found: {filename}")
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data.get("messages", [])
    except Exception as e:
        print(f"Error loading conversation: {e}")
        return None


def list_conversations() -> list:
    """List available saved conversations."""
    try:
        save_dir = Path("./conversations")
        if not save_dir.exists():
            return []
        
        files = sorted(save_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [f.name for f in files]
    except Exception:
        return []
