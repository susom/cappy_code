# Cappy Code API Documentation

## Overview

Cappy Code provides a comprehensive API for building PHI-safe agentic coding assistants. This document covers all public APIs and their usage.

---

## Core Modules

### `cappy.tools`

Low-level tool functions for file and code operations.

#### `scan(path: str) -> dict`

Scan a directory and return file structure.

**Parameters:**
- `path` (str): Root path to scan

**Returns:**
- `dict` with keys:
  - `root` (str): Absolute path scanned
  - `total_files` (int): Number of files found
  - `total_dirs` (int): Number of directories
  - `by_extension` (dict): File counts by extension
  - `tree` (list): List of file paths
  - `truncated` (bool): Whether results were truncated

**Example:**
```python
from cappy import tools

result = tools.scan("./my_project")
print(f"Found {result['total_files']} files")
```

---

#### `search(pattern: str, path: str = ".", max_results: int = 50) -> dict`

Search for regex pattern in files.

**Parameters:**
- `pattern` (str): Regex pattern to search
- `path` (str): Root path to search (default: ".")
- `max_results` (int): Maximum matches to return (default: 50)

**Returns:**
- `dict` with keys:
  - `pattern` (str): The search pattern
  - `search_path` (str): Path searched
  - `matches` (list): List of match dicts with `file`, `line_num`, `line`
  - `total_matches` (int): Total matches found
  - `truncated` (bool): Whether results were truncated

**Example:**
```python
result = tools.search(r"def\s+\w+", "./src")
for match in result['matches']:
    print(f"{match['file']}:{match['line_num']}: {match['line']}")
```

---

#### `read(filepath: str, start: int = 1, limit: Optional[int] = None) -> dict`

Read file contents.

**Parameters:**
- `filepath` (str): Path to file
- `start` (int): Starting line number (1-indexed, default: 1)
- `limit` (Optional[int]): Maximum lines to read (default: None = all)

**Returns:**
- `dict` with keys:
  - `content` (str): File contents
  - `total_lines` (int): Total lines in file
  - `start` (int): Starting line
  - `end` (int): Ending line
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.read("main.py", start=10, limit=20)
print(result['content'])
```

---

#### `write(filepath: str, content: str, overwrite: bool = False, create_snapshot: bool = True) -> dict`

Write content to file.

**Parameters:**
- `filepath` (str): Path to file
- `content` (str): Content to write
- `overwrite` (bool): Allow overwriting existing files (default: False)
- `create_snapshot` (bool): Create undo snapshot (default: True)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether write succeeded
  - `file` (str): Absolute file path
  - `bytes_written` (int): Bytes written
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.write("new_file.py", "print('hello')", overwrite=False)
if result['success']:
    print(f"Wrote {result['bytes_written']} bytes")
```

---

#### `edit(filepath: str, old_string: str, new_string: str, create_snapshot: bool = True) -> dict`

Perform surgical edit on a file.

**Parameters:**
- `filepath` (str): Path to file
- `old_string` (str): Exact string to find and replace
- `new_string` (str): Replacement string
- `create_snapshot` (bool): Create undo snapshot (default: True)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether edit succeeded
  - `file` (str): Absolute file path
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.edit("main.py", "hello", "goodbye")
if result['success']:
    print("Edit successful")
```

---

#### `delete(filepath: str, confirm: bool = False, create_snapshot: bool = True) -> dict`

Delete a file or directory.

**Parameters:**
- `filepath` (str): Path to file/directory
- `confirm` (bool): Must be True to actually delete (default: False)
- `create_snapshot` (bool): Create undo snapshot (default: True)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether delete succeeded
  - `file` (str): Absolute file path
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.delete("old_file.txt", confirm=True)
if result['success']:
    print("File deleted")
```

---

#### `move(src: str, dst: str, overwrite: bool = False) -> dict`

Move or rename a file/directory.

**Parameters:**
- `src` (str): Source path
- `dst` (str): Destination path
- `overwrite` (bool): Allow overwriting destination (default: False)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether move succeeded
  - `src` (str): Source path
  - `dst` (str): Destination path
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.move("old_name.py", "new_name.py")
```

---

#### `copy(src: str, dst: str, overwrite: bool = False) -> dict`

Copy a file or directory.

**Parameters:**
- `src` (str): Source path
- `dst` (str): Destination path
- `overwrite` (bool): Allow overwriting destination (default: False)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether copy succeeded
  - `src` (str): Source path
  - `dst` (str): Destination path
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.copy("template.py", "new_file.py")
```

---

#### `run(cmd: str, timeout: int = 60, cwd: Optional[str] = None, allow_dangerous: bool = False) -> dict`

Run a shell command.

**Parameters:**
- `cmd` (str): Shell command to execute
- `timeout` (int): Timeout in seconds (default: 60)
- `cwd` (Optional[str]): Working directory (default: current directory)
- `allow_dangerous` (bool): Allow dangerous commands (default: False)

**Returns:**
- `dict` with keys:
  - `exit_code` (int): Command exit code
  - `stdout` (str): Standard output
  - `stderr` (str): Standard error
  - `command` (str): Command executed
  - `warning` (str): Warning if dangerous command allowed
  - `error` (str): Error message if failed

**Example:**
```python
result = tools.run("ls -la", cwd="/tmp")
print(result['stdout'])
```

---

### `cappy.config`

Configuration management.

#### `CappyConfig` (dataclass)

Type-safe configuration object with validation.

**Fields:**
```python
default_model: str = "o1"
allowed_models: List[str] = ["gpt-4.1", "o1", "gemini25pro"]
max_files_touched_per_run: int = 5
max_iterations: int = 20
max_tool_calls_per_session: int = 50
api_timeout: int = 120
require_plan: bool = True
block_dangerous_commands: bool = True
log_dir: str = "./logs"
auto_snapshot: bool = True
```

**Methods:**
- `validate() -> List[str]`: Validate configuration, returns list of errors

---

#### `get_config(reload: bool = False) -> dict`

Get configuration dictionary.

**Parameters:**
- `reload` (bool): Force reload from file (default: False)

**Returns:**
- `dict`: Configuration dictionary

---

#### `get_typed_config(reload: bool = False) -> CappyConfig`

Get type-safe configuration object.

**Parameters:**
- `reload` (bool): Force reload from file (default: False)

**Returns:**
- `CappyConfig`: Configuration object

---

#### `validate_config(config_path: Optional[str] = None) -> tuple[bool, List[str]]`

Validate configuration file.

**Parameters:**
- `config_path` (Optional[str]): Path to config file (default: auto-find)

**Returns:**
- `tuple`: (is_valid, list_of_errors)

**Example:**
```python
from cappy.config import validate_config

is_valid, errors = validate_config("my_config.yaml")
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

---

### `cappy.undo`

Undo/rollback system using git.

#### `UndoManager`

Manages git-based snapshots for undo functionality.

**Methods:**

##### `snapshot(message: str) -> bool`

Create a snapshot of current state.

**Parameters:**
- `message` (str): Snapshot description

**Returns:**
- `bool`: Success

---

##### `undo() -> tuple[bool, str]`

Undo last change by popping git stash.

**Returns:**
- `tuple`: (success, message)

---

##### `list_snapshots() -> List[dict]`

List available snapshots.

**Returns:**
- `List[dict]`: List of snapshot info dicts

---

#### `get_undo_manager() -> UndoManager`

Get global undo manager instance.

**Example:**
```python
from cappy.undo import get_undo_manager

undo_mgr = get_undo_manager()
undo_mgr.snapshot("Before major changes")

# ... make changes ...

success, msg = undo_mgr.undo()
print(msg)
```

---

### `cappy.analytics`

Log analysis and usage statistics.

#### `LogAnalyzer`

Analyze JSONL logs for usage patterns.

**Methods:**

##### `__init__(log_dir: str = "./logs")`

Initialize analyzer.

---

##### `tool_usage_stats(days: Optional[int] = None) -> Dict`

Get tool usage statistics.

**Parameters:**
- `days` (Optional[int]): Only analyze last N days

**Returns:**
- `dict` with usage stats

---

##### `session_stats(days: Optional[int] = None) -> Dict`

Get session statistics.

---

##### `error_analysis(days: Optional[int] = None) -> Dict`

Analyze errors in logs.

---

##### `performance_summary(days: Optional[int] = None) -> Dict`

Get performance metrics.

---

##### `generate_report(days: Optional[int] = 7) -> str`

Generate comprehensive usage report.

**Example:**
```python
from cappy.analytics import LogAnalyzer

analyzer = LogAnalyzer(log_dir="./logs")
report = analyzer.generate_report(days=7)
print(report)
```

---

### `cappy.performance`

Performance monitoring.

#### `PerformanceMonitor`

Monitor performance metrics.

**Methods:**

##### `measure(operation: str)` (context manager)

Measure operation performance.

**Example:**
```python
from cappy.performance import get_monitor

monitor = get_monitor()

with monitor.measure("my_operation") as metrics:
    # ... do work ...
    pass

summary = monitor.get_summary()
print(f"Avg duration: {summary['avg_duration_ms']}ms")
```

---

#### `get_system_info() -> Dict`

Get current system resource usage.

**Returns:**
- `dict` with CPU, memory, thread info

---

### `cappy.ui`

Terminal UI utilities.

#### Color Functions

- `success(text: str) -> str`: Format success message (green)
- `error(text: str) -> str`: Format error message (red)
- `warning(text: str) -> str`: Format warning message (yellow)
- `info(text: str) -> str`: Format info message (blue)
- `highlight(text: str) -> str`: Highlight text (cyan)

#### `ProgressBar`

Simple progress bar for terminal.

**Example:**
```python
from cappy.ui import ProgressBar

progress = ProgressBar(total=100, prefix="Processing")
for i in range(100):
    # ... do work ...
    progress.update(1)
progress.finish()
```

#### `print_table(headers: list, rows: list, align: Optional[list] = None)`

Print formatted table.

**Example:**
```python
from cappy.ui import print_table

headers = ["Name", "Count", "Percent"]
rows = [
    ["scan", 42, "35%"],
    ["read", 30, "25%"],
]
print_table(headers, rows, align=['left', 'right', 'right'])
```

---

## CLI Commands

### `cappy scan [path]`

Scan repository structure.

### `cappy search <pattern> [path]`

Search for pattern in files.

### `cappy read <file>`

Read file contents.

### `cappy run <command>`

Run shell command.

### `cappy agent <task>`

Run agentic loop for a task.

### `cappy chat`

Interactive chat with tools.

### `cappy config validate`

Validate configuration file.

### `cappy analytics [--days N]`

Analyze usage logs.

---

## Configuration File

`cappy_config.yaml`:

```yaml
# Model settings
default_model: o1
allowed_models:
  - gpt-4.1
  - o1
  - gemini25pro

# Limits
max_files_touched_per_run: 5
max_iterations: 20
max_tool_calls_per_session: 50

# Timeouts (seconds)
api_timeout: 120
default_command_timeout: 60

# Retry settings
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

---

## Error Handling

All tool functions return dicts with consistent error handling:

```python
result = tools.read("nonexistent.txt")
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(result['content'])
```

---

## Best Practices

1. **Always check for errors** in tool results
2. **Use snapshots** before destructive operations
3. **Validate config** before deployment
4. **Monitor logs** with analytics
5. **Set appropriate timeouts** for long operations
6. **Use typed config** for type safety

---

## See Also

- [Architecture Guide](ARCHITECTURE.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Examples](../examples/)
