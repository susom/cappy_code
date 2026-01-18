# Cappy Code Architecture

## Overview

Cappy Code is a modular, PHI-safe agentic coding assistant built with security, reliability, and extensibility in mind.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                     (CLI / Chat / API)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Planning   │  │  Execution   │  │  Reflection  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       Tool Layer                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ scan │ │search│ │ read │ │write │ │ edit │ │ run  │   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │delete│ │ move │ │ copy │ │apply │                      │
│  └──────┘ └──────┘ └──────┘ └──────┘                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Support Systems                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Logging    │  │     Undo     │  │  Analytics   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Config    │  │ Performance  │  │      UI      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ SecureChatAI │  │  File System │  │     Git      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure

### Core Modules

#### `cappy/agent.py`
**Responsibility**: Agentic loop orchestration

- System prompt generation
- Response parsing
- Tool execution routing
- Iteration management

**Key Functions**:
- `get_system_prompt()`: Generate system prompt with tools
- `parse_agent_response()`: Parse AI JSON responses
- `execute_tool()`: Route tool calls to implementations
- `run_agent()`: Main agentic loop

---

#### `cappy/tools.py`
**Responsibility**: Low-level file and code operations

- File I/O (read, write, edit)
- Directory scanning
- Code search
- Command execution
- File management (delete, move, copy)

**Safety Features**:
- Dangerous command detection
- Overwrite protection
- Automatic snapshots
- Path validation

---

#### `cappy/ai_client.py`
**Responsibility**: AI API communication

- OpenAI-compatible API client
- Retry logic with exponential backoff
- Token counting
- Model management

**Features**:
- 3 retries by default
- Smart retry (5xx yes, 4xx no)
- Timeout handling
- Error categorization

---

#### `cappy/chat.py`
**Responsibility**: Interactive chat interface

- REPL loop
- Command handling
- Conversation management
- Save/load functionality

**Commands**:
- `/help`, `/save`, `/load`
- `/undo`, `/snapshots`
- `/clear`, `/model`, `/quit`

---

### Support Modules

#### `cappy/config.py`
**Responsibility**: Configuration management

- YAML config loading
- Type-safe dataclass
- Validation
- Default values

**Config Hierarchy**:
1. Default values (in code)
2. YAML file (cappy_config.yaml)
3. Environment variables (future)

---

#### `cappy/logger.py`
**Responsibility**: Structured logging

- JSONL format for machine parsing
- Human-readable format for debugging
- Separate log files
- Session tracking

**Log Types**:
- `tool_call`: Tool execution logs
- `simple_line`: Human-readable logs

---

#### `cappy/undo.py`
**Responsibility**: Undo/rollback system

- Git-based snapshots
- Automatic snapshot creation
- Undo via git stash pop
- Snapshot listing

**Workflow**:
1. Before destructive operation → `snapshot()`
2. Operation executes
3. If mistake → `/undo` command
4. Git stash pop restores state

---

#### `cappy/analytics.py`
**Responsibility**: Log analysis

- Tool usage statistics
- Session analytics
- Error analysis
- Performance metrics

**Reports**:
- Tool call frequency
- Average durations
- Error rates
- Slow operations

---

#### `cappy/performance.py`
**Responsibility**: Performance monitoring

- Operation timing
- Memory tracking
- CPU usage
- System resource info

**Usage**:
```python
with monitor.measure("operation"):
    # ... work ...
    pass
```

---

#### `cappy/ui.py`
**Responsibility**: Terminal UI utilities

- Colored output
- Progress bars
- Spinners
- Table formatting
- Box drawing

---

### Entry Points

#### `cappy/cli.py`
**Responsibility**: Command-line interface

- Argument parsing
- Command routing
- Main entry point

**Commands**:
- Direct tool calls (scan, search, read, etc.)
- Agent mode
- Chat mode
- Config management
- Analytics

---

## Data Flow

### Agent Loop Flow

```
User Input
    │
    ▼
┌─────────────────┐
│ Parse Request   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate Prompt │ ← System Prompt + History
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Call AI API    │ ← SecureChatAI
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Parse Response  │ → JSON Schema Validation
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│   Tool Call     │  │      Done       │
└────────┬────────┘  └────────┬────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐     Return Result
│  Execute Tool   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Log Result    │
└────────┬────────┘
         │
         ▼
    Loop Back
```

---

### Tool Execution Flow

```
Tool Call
    │
    ▼
┌─────────────────┐
│ Validate Input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Safety Check   │ ← Dangerous patterns, overwrite protection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Snapshot │ ← If destructive operation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute Action  │ ← File I/O, command execution
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Log Result     │ ← JSONL + human logs
└────────┬────────┘
         │
         ▼
   Return Result
```

---

## Security Model

### PHI Safety

**No Data Exfiltration**:
- All operations local
- No external API calls from tools
- AI API only receives code context, not PHI

**Audit Trail**:
- All operations logged
- JSONL format for compliance
- Session tracking
- Timestamp on every action

---

### Command Safety

**Dangerous Pattern Detection**:
```python
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r'sudo\s+rm',
    r'dd\s+if=',
    r':(\){\s*:|:&\s*\};:',  # Fork bomb
    r'curl.*\|\s*bash',
    r'chmod\s+777',
]
```

**Protection Layers**:
1. Pattern matching
2. Explicit `allow_dangerous` flag required
3. Warning in output if allowed
4. Logged for audit

---

### File Safety

**Overwrite Protection**:
- `write()` requires `overwrite=True` for existing files
- `move()` and `copy()` require `overwrite=True` for existing destinations
- `delete()` requires `confirm=True`

**Undo System**:
- Automatic snapshots before destructive ops
- Git-based rollback
- `/undo` command in chat
- Snapshot history

---

## Configuration

### Config File Structure

```yaml
# Model settings
default_model: o1
allowed_models: [gpt-4.1, o1, gemini25pro]

# Limits
max_files_touched_per_run: 5
max_iterations: 20
max_tool_calls_per_session: 50

# Timeouts
api_timeout: 120
default_command_timeout: 60

# Retry
api_retry_attempts: 3
api_retry_backoff: 2.0

# Safety
require_plan: true
block_dangerous_commands: true

# Paths
log_dir: ./logs
conversation_dir: ./conversations

# Undo
auto_snapshot: true
```

### Config Loading

1. Load defaults from `CappyConfig` dataclass
2. Search for `cappy_config.yaml` (walk up directories)
3. Merge file config over defaults
4. Validate with `CappyConfig.validate()`
5. Cache in memory

---

## Logging

### JSONL Format

```json
{
  "type": "tool_call",
  "tool_name": "read",
  "inputs": {"path": "main.py"},
  "result": {"content": "...", "total_lines": 42},
  "success": true,
  "duration_ms": 15.3,
  "timestamp": "2026-01-18T10:30:00",
  "session_id": "abc123"
}
```

### Log Files

- `{log_dir}/cappy_{date}.jsonl` - Machine-readable
- `{log_dir}/cappy_{date}.log` - Human-readable

---

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_tools.py       # Unit tests for tools
├── test_agent.py       # Integration tests for agent
├── test_config.py      # Unit tests for config
└── test_analytics.py   # Unit tests for analytics
```

### Running Tests

```bash
pytest tests/ -v --cov=cappy
```

### Coverage Goals

- Tools: 80%+
- Config: 90%+
- Agent: 70%+
- Overall: 75%+

---

## Performance

### Optimization Strategies

1. **Lazy Loading**: Modules loaded on demand
2. **Caching**: Config cached in memory
3. **Streaming**: Large files read in chunks
4. **Parallel**: Future support for parallel tool calls

### Monitoring

- `PerformanceMonitor` tracks all operations
- Memory delta per operation
- CPU usage tracking
- Slow operation detection (>5s)

---

## Extensibility

### Adding New Tools

1. Implement function in `tools.py`
2. Add to `AGENT_RESPONSE_SCHEMA` in `agent.py`
3. Add handler in `execute_tool()` in `agent.py`
4. Update system prompt in `get_system_prompt()`
5. Add tests in `tests/test_tools.py`

**Example**:
```python
def my_new_tool(arg1: str, arg2: int) -> dict:
    """Tool description."""
    try:
        # ... implementation ...
        return {"success": True, "result": "..."}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### Adding New Commands

1. Add command handler in `cli.py`
2. Add subparser in `main()` in `cli.py`
3. Update help text

---

## Deployment

### Installation

```bash
pip install -e .
```

### Configuration

1. Copy `cappy_config.yaml` to project root
2. Customize settings
3. Validate: `cappy config validate`

### Bash Completion

```bash
source completion/cappy-completion.bash
```

---

## Future Enhancements

### Planned Features

1. **Parallel Tool Execution**: Execute independent tools in parallel
2. **Semantic Search**: Use embeddings for better code search
3. **Web Interface**: Browser-based UI
4. **Plugin System**: Third-party tool plugins
5. **Multi-Agent**: Collaborate with multiple AI agents
6. **CI/CD Integration**: GitHub Actions, GitLab CI
7. **Docker Support**: Containerized deployment

---

## See Also

- [API Documentation](API.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Examples](../examples/)
