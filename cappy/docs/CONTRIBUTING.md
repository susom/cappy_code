# Contributing to Cappy Code

Thank you for your interest in contributing to Cappy Code! This guide will help you get started.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Basic understanding of agentic AI systems

### Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourorg/cappy-code.git
cd cappy-code
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Install in development mode**
```bash
pip install -e .
```

4. **Run tests**
```bash
pytest tests/ -v
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Changes

Follow the coding standards (see below).

### 3. Write Tests

All new features must include tests:
- Unit tests for individual functions
- Integration tests for workflows
- Aim for 80%+ coverage

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=cappy --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v
```

### 5. Update Documentation

- Update API docs if adding/changing public APIs
- Update ARCHITECTURE.md if changing system design
- Add examples if applicable

### 6. Commit Changes

```bash
git add .
git commit -m "feat: add new tool for X"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 7. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

**Formatting**:
- 4 spaces for indentation
- Max line length: 100 characters
- Use `black` for auto-formatting

**Naming**:
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Type Hints**:
```python
def my_function(arg1: str, arg2: int) -> dict:
    """Function docstring."""
    pass
```

**Docstrings**:
```python
def my_function(arg1: str, arg2: int) -> dict:
    """
    Brief one-line description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When X happens
    """
    pass
```

### Code Organization

**Module Structure**:
```python
# Standard library imports
import os
import sys

# Third-party imports
import yaml
from openai import OpenAI

# Local imports
from cappy.config import get_config
from cappy.logger import log_action
```

**Function Length**:
- Keep functions under 50 lines
- Extract complex logic into helper functions
- One function = one responsibility

**Error Handling**:
```python
def my_tool(arg: str) -> dict:
    """Tool description."""
    try:
        # ... implementation ...
        return {"success": True, "result": "..."}
    except SpecificException as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
```

---

## Adding New Tools

### 1. Implement Tool Function

Add to `cappy/tools.py`:

```python
def my_new_tool(arg1: str, arg2: int = 10) -> dict:
    """
    Brief description of what the tool does.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 10)
    
    Returns:
        dict with keys:
            - success: bool
            - result: any (if successful)
            - error: str (if failed)
    """
    try:
        # Validate inputs
        if not arg1:
            return {"success": False, "error": "arg1 is required"}
        
        # Create snapshot if destructive
        if is_destructive_operation:
            try:
                from cappy.undo import get_undo_manager
                undo_mgr = get_undo_manager()
                undo_mgr.snapshot(f"Before my_new_tool on {arg1}")
            except Exception:
                pass
        
        # Perform operation
        result = do_the_work(arg1, arg2)
        
        return {
            "success": True,
            "result": result,
            "arg1": arg1,
            "arg2": arg2,
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Update Agent Schema

Add to `AGENT_RESPONSE_SCHEMA` in `cappy/agent.py`:

```python
"tool_name": {
    "type": "string",
    "enum": [
        "scan", "search", "read", "write", "edit",
        "delete", "move", "copy", "apply", "run",
        "my_new_tool"  # Add here
    ]
}
```

### 3. Add Tool Handler

Add to `execute_tool()` in `cappy/agent.py`:

```python
elif tool_name == "my_new_tool":
    arg1 = inputs.get("arg1")
    arg2 = inputs.get("arg2", 10)
    result = tools.my_new_tool(arg1=arg1, arg2=arg2)
```

### 4. Update System Prompt

Add to `get_system_prompt()` in `cappy/agent.py`:

```python
tools_desc.append("""
10. my_new_tool(arg1, arg2=10)
   Description of what it does.
   
   Inputs:
   - arg1 (string, required): Description
   - arg2 (integer, optional): Description (default: 10)
   
   Returns:
   - success: bool
   - result: any
   - error: str (if failed)
   
   Example:
   {"tool_name": "my_new_tool", "inputs": {"arg1": "value", "arg2": 20}}
""")
```

### 5. Add CLI Command (Optional)

Add to `cappy/cli.py`:

```python
def cmd_my_new_tool(args):
    """Handle my_new_tool command."""
    result = tools.my_new_tool(arg1=args.arg1, arg2=args.arg2)
    
    if result.get("success"):
        print(f"Success: {result['result']}")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

# In main():
p_my_new_tool = subparsers.add_parser("my_new_tool", help="Description")
p_my_new_tool.add_argument("arg1", help="Description")
p_my_new_tool.add_argument("--arg2", type=int, default=10, help="Description")
p_my_new_tool.set_defaults(func=cmd_my_new_tool)
```

### 6. Write Tests

Add to `tests/test_tools.py`:

```python
class TestMyNewTool:
    """Tests for my_new_tool."""
    
    @pytest.mark.unit
    def test_basic(self):
        """Test basic functionality."""
        result = tools.my_new_tool(arg1="test", arg2=20)
        
        assert result["success"]
        assert result["result"] == expected_value
    
    @pytest.mark.unit
    def test_missing_arg1(self):
        """Test error when arg1 missing."""
        result = tools.my_new_tool(arg1="", arg2=10)
        
        assert not result["success"]
        assert "required" in result["error"]
    
    @pytest.mark.unit
    def test_default_arg2(self):
        """Test default value for arg2."""
        result = tools.my_new_tool(arg1="test")
        
        assert result["success"]
        assert result["arg2"] == 10
```

### 7. Update Documentation

Add to `docs/API.md`:

```markdown
#### `my_new_tool(arg1: str, arg2: int = 10) -> dict`

Brief description.

**Parameters:**
- `arg1` (str): Description
- `arg2` (int): Description (default: 10)

**Returns:**
- `dict` with keys:
  - `success` (bool): Whether operation succeeded
  - `result` (any): Result if successful
  - `error` (str): Error message if failed

**Example:**
\`\`\`python
result = tools.my_new_tool(arg1="test", arg2=20)
if result['success']:
    print(result['result'])
\`\`\`
```

---

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
@pytest.mark.unit
def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result["success"]
    assert result["value"] == expected
```

### Integration Tests

Test workflows and interactions:

```python
@pytest.mark.integration
def test_agent_workflow():
    """Test full agent workflow."""
    # Setup
    task = "Test task"
    
    # Execute
    result = run_agent(task, max_iterations=5)
    
    # Verify
    assert result["status"] == "completed"
```

### Fixtures

Use pytest fixtures for common setup:

```python
@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    
    (project_dir / "main.py").write_text("print('hello')")
    (project_dir / "README.md").write_text("# Test")
    
    return project_dir
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit        # Unit test
@pytest.mark.integration # Integration test
@pytest.mark.slow        # Slow test (>1s)
@pytest.mark.skip        # Skip test
```

Run specific markers:
```bash
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Exclude slow tests
```

---

## Documentation Guidelines

### API Documentation

- Document all public functions
- Include parameter types and descriptions
- Provide usage examples
- Document return values
- Note any exceptions raised

### Architecture Documentation

- Update ARCHITECTURE.md when changing system design
- Include diagrams for complex flows
- Explain design decisions
- Document security considerations

### Examples

Add examples to `examples/` directory:

```python
"""
Example: Using my_new_tool

This example demonstrates how to use my_new_tool for X.
"""

from cappy import tools

# Basic usage
result = tools.my_new_tool(arg1="test")
print(result)

# Advanced usage
result = tools.my_new_tool(arg1="test", arg2=20)
if result['success']:
    print(f"Result: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

---

## Code Review Process

### Checklist

Before submitting a PR, ensure:

- [ ] All tests pass
- [ ] Coverage is maintained or improved
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No debugging code left in
- [ ] No secrets or credentials committed

### Review Criteria

Reviewers will check:

1. **Correctness**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Style**: Does it follow coding standards?
4. **Documentation**: Is it well-documented?
5. **Security**: Are there security implications?
6. **Performance**: Are there performance concerns?

---

## Release Process

### Version Numbering

Follow Semantic Versioning (semver):
- `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (patch: bug fixes)
- `1.0.0` → `1.1.0` (minor: new features, backward compatible)
- `1.0.0` → `2.0.0` (major: breaking changes)

### Release Steps

1. Update version in `cappy/__init__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. Create GitHub release
6. Publish to PyPI (if applicable)

---

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Email**: contact@yourorg.com

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Cappy Code! 🎉
