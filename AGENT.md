# Cappy Code - Agent Runner Documentation

PHI-safe agentic code runner CLI for use with SecureChatAI backend.

## Quick Start

```bash
# Interactive chat mode (like Claude Code)
cappy chat

# One-shot agentic task
cappy agent "add error handling to main.py"

# Direct tool usage
cappy scan [path]
cappy search <pattern> [path]
cappy read <filepath>
```

## Primary Commands

### chat
Interactive REPL with Claude Code-like experience.
```bash
cappy chat
```
Features:
- Multi-turn conversation with SecureChatAI
- Automatic tool calling (scan, search, read, write, edit, apply, run)
- Project context from `CAPPY.md` in current directory
- Commands: `/help`, `/paste`, `/clear`, `/model [name]`, `/quit`

### agent
One-shot task execution with agentic loop.
```bash
cappy agent "your task description"
```
Agent autonomously uses tools to complete the task, then exits.

## Available Tools

### scan
Scan repository and print file summary.
```bash
cappy scan [path]
```
Output: JSON with `total_files`, `total_dirs`, `by_extension`, `tree`

### search
Search for regex pattern in file contents.
```bash
cappy search <pattern> [path] [--max N]
```
Output: JSON with `matches` (file, line_num, line)

### read
Read file contents with optional line range.
```bash
cappy read <path> [--start N] [--limit N]
```
Output: Numbered file content with JSON metadata header

### write
Create or overwrite a file with new content.
```bash
cappy write <path> "<content>"
```
Safety: Warns if file exists (use `--force` to overwrite)

### edit
Surgical string replacement in a file.
```bash
cappy edit <path> --old "<old_string>" --new "<new_string>"
```
Safety: Validates `old_string` exists and is unique before replacing

### apply
Apply a unified diff patch file.
```bash
cappy apply <patch.diff> [--max-files N]
```
Safety checks:
- Refuses if patch touches more files than `max_files_touched_per_run` (config)
- Refuses if target files don't exist (no blind file creation)
- Runs `--dry-run` before applying

### run
Execute a shell command and capture output.
```bash
cappy run "<command>" [--timeout N]
```
Output: JSON with `exit_code`, `stdout`, `stderr`

## Configuration

Create `cappy_config.yaml` in your project root:

```yaml
# Allowed LLM models for the agent backend
allowed_models:
  - gpt-4.1

# Max files a single patch can touch (safety limit)
max_files_touched_per_run: 5

# Require explicit plan approval before code changes
require_plan: true

# Verification command (optional)
verify_command: "pytest"  # or "npm test", "make test", etc.

# Log directory
log_dir: "./logs"
```

The CLI searches for config starting from cwd and walking up.

## Logging

All tool invocations are logged to `./logs/cappy_YYYY-MM-DD.jsonl` (JSON lines format).

Each entry contains:
- `ts`: ISO timestamp (UTC)
- `action`: Tool name (scan, search, read, apply, run)
- `inputs`: Input arguments (sensitive fields redacted)
- `output`: Result (truncated if large)
- `success`: Boolean
- `duration_ms`: Execution time

Example log entry:
```json
{"ts": "2026-01-08T00:21:03.490408+00:00", "action": "scan", "inputs": {"path": "."}, "output": {"total_files": 5}, "success": true, "duration_ms": 0.17}
```

## SecureChatAI Integration

Cappy Code is fully integrated with SecureChatAI (REDCap External Module API).

**Setup:**
1. Copy `.env.example` to `.env`
2. Add your credentials:
   - `REDCAP_API_URL`: Your SecureChatAI endpoint
   - `REDCAP_API_TOKEN`: Your API token
3. Start chatting: `cappy chat`

**How it works:**
- Local CLI executes tools (scan, read, write, etc.)
- SecureChatAI backend acts as the "brain" (model inference)
- JSON schema enforcement ensures reliable tool calling
- All data stays local (PHI-safe)

## Safety Rules

1. **No exfiltration**: Logs stay local, no telemetry
2. **File limits**: `max_files_touched_per_run` enforced on patches
3. **No blind writes**: `apply` requires target files to exist
4. **Audit trail**: Every action logged with inputs/outputs
5. **Sensitive redaction**: Passwords, tokens, secrets redacted from logs
6. **Timeout protection**: Commands timeout after 60s (configurable)

## Limitations

- `apply` only works with unified diff format (`diff -u` or `git diff`)
- `apply` requires the `patch` command on system PATH
- Binary files are skipped during `search`
- `scan` limits tree output to 200 files
- `search` limits results to 50 matches (configurable via `--max`)
