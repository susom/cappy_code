"""Core tool implementations for the Cappy Code runner."""

import fnmatch
import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def load_cappyignore(root: Path) -> list[str]:
    """
    Load .cappyignore patterns from root directory.

    Returns list of glob patterns to ignore.
    """
    ignore_file = root / ".cappyignore"
    patterns = []

    if ignore_file.exists():
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except (OSError, IOError):
            pass

    return patterns


def should_ignore(path: str, patterns: list[str]) -> bool:
    """
    Check if a path matches any ignore pattern.

    Supports glob patterns like *.log, node_modules/, etc.
    """
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(path, dir_pattern) or fnmatch.fnmatch(path, f"*/{dir_pattern}"):
                return True
            if f"/{dir_pattern}/" in f"/{path}/" or path.startswith(f"{dir_pattern}/"):
                return True
        else:
            # File pattern
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
    return False


def scan(root: str = ".") -> dict:
    """
    Scan repository and return a summary map.

    Returns dict with:
        - total_files: int
        - total_dirs: int
        - by_extension: dict[str, int]
        - tree: list of relative paths (limited to first 200)
    """
    root_path = Path(root).resolve()

    if not root_path.exists():
        return {"error": f"Path does not exist: {root}"}

    # Load .cappyignore patterns
    ignore_patterns = load_cappyignore(root_path)

    total_files = 0
    total_dirs = 0
    by_extension: dict[str, int] = {}
    tree: list[str] = []

    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "vendor", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "coverage", ".cache"
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden and build directories
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]

        rel_dir = Path(dirpath).relative_to(root_path)
        total_dirs += 1

        for fname in filenames:
            if fname.startswith("."):
                continue

            rel_path = str(rel_dir / fname) if str(rel_dir) != "." else fname

            # Check .cappyignore
            if should_ignore(rel_path, ignore_patterns):
                continue

            total_files += 1
            ext = Path(fname).suffix or "(no ext)"
            by_extension[ext] = by_extension.get(ext, 0) + 1

            if len(tree) < 200:
                tree.append(rel_path)

    return {
        "root": str(root_path),
        "total_files": total_files,
        "total_dirs": total_dirs,
        "by_extension": dict(sorted(by_extension.items(), key=lambda x: -x[1])),
        "tree": sorted(tree),
        "truncated": total_files > 200,
    }


def search(pattern: str, path: str = ".", max_results: int = 50) -> dict:
    """
    Search for files matching a regex pattern in content or filename.

    Returns dict with:
        - matches: list of {file, line_num, line} dicts
        - total_matches: int
        - truncated: bool
    """
    root_path = Path(path).resolve()

    if not root_path.exists():
        return {"error": f"Path does not exist: {path}"}

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"error": f"Invalid regex pattern: {e}"}

    # Load .cappyignore patterns
    ignore_patterns = load_cappyignore(root_path)

    matches: list[dict] = []
    total_matches = 0

    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "vendor", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "coverage", ".cache"
    }

    binary_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip",
        ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".woff",
        ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".mov", ".avi"
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]

        for fname in filenames:
            if fname.startswith("."):
                continue

            fpath = Path(dirpath) / fname
            rel_path = str(fpath.relative_to(root_path))

            # Check .cappyignore
            if should_ignore(rel_path, ignore_patterns):
                continue

            # Skip binary files
            if fpath.suffix.lower() in binary_extensions:
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            total_matches += 1
                            if len(matches) < max_results:
                                matches.append({
                                    "file": rel_path,
                                    "line_num": line_num,
                                    "line": line.rstrip()[:200],
                                })
            except (OSError, IOError):
                continue

    return {
        "pattern": pattern,
        "search_path": str(root_path),
        "matches": matches,
        "total_matches": total_matches,
        "truncated": total_matches > max_results,
    }


def read(filepath: str, start: int = 1, limit: Optional[int] = None) -> dict:
    """
    Read a file and return its contents.

    Args:
        filepath: Path to file
        start: Line number to start from (1-indexed)
        limit: Max lines to return (None = all)

    Returns dict with:
        - content: str (the file contents)
        - total_lines: int
        - start: int
        - end: int
    """
    fpath = Path(filepath).resolve()

    if not fpath.exists():
        return {"error": f"File does not exist: {filepath}"}

    if not fpath.is_file():
        return {"error": f"Path is not a file: {filepath}"}

    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except (OSError, IOError) as e:
        return {"error": f"Cannot read file: {e}"}

    total_lines = len(all_lines)
    start_idx = max(0, start - 1)  # Convert to 0-indexed

    if limit is not None:
        end_idx = min(start_idx + limit, total_lines)
    else:
        end_idx = total_lines

    selected_lines = all_lines[start_idx:end_idx]

    # Format with line numbers
    numbered_lines = []
    for i, line in enumerate(selected_lines, start=start_idx + 1):
        numbered_lines.append(f"{i:6d}  {line.rstrip()}")

    return {
        "file": str(fpath),
        "content": "\n".join(numbered_lines),
        "total_lines": total_lines,
        "start": start_idx + 1,
        "end": end_idx,
    }


def write(filepath: str, content: str, overwrite: bool = False) -> dict:
    """
    Write content to a file.

    Args:
        filepath: Path to file (will create parent directories)
        content: Content to write
        overwrite: If False, refuse to overwrite existing files

    Returns dict with:
        - success: bool
        - file: str (absolute path)
        - bytes_written: int
        - error: str (if failed)
    """
    fpath = Path(filepath).resolve()

    # Safety: don't overwrite unless explicitly allowed
    if fpath.exists() and not overwrite:
        return {
            "success": False,
            "error": f"File already exists: {filepath}. Set overwrite=true to replace.",
        }

    # Create parent directories if needed
    try:
        fpath.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, IOError) as e:
        return {"success": False, "error": f"Cannot create directory: {e}"}

    # Write the file
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "file": str(fpath),
            "bytes_written": len(content.encode("utf-8")),
        }
    except (OSError, IOError) as e:
        return {"success": False, "error": f"Cannot write file: {e}"}


def edit(filepath: str, old_string: str, new_string: str) -> dict:
    """
    Perform surgical edit on a file by replacing old_string with new_string.

    Args:
        filepath: Path to file to edit
        old_string: Exact string to find and replace
        new_string: String to replace it with

    Returns dict with:
        - success: bool
        - file: str (absolute path)
        - error: str (if failed)

    Errors:
        - File doesn't exist
        - old_string not found in file
        - old_string appears multiple times (ambiguous)
    """
    fpath = Path(filepath).resolve()

    if not fpath.exists():
        return {"success": False, "error": f"File does not exist: {filepath}"}

    if not fpath.is_file():
        return {"success": False, "error": f"Path is not a file: {filepath}"}

    # Read current content
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (OSError, IOError) as e:
        return {"success": False, "error": f"Cannot read file: {e}"}

    # Check if old_string exists
    if old_string not in content:
        return {
            "success": False,
            "error": f"old_string not found in {filepath}. Make sure it matches exactly (including whitespace)."
        }

    # Check if old_string is unique
    count = content.count(old_string)
    if count > 1:
        return {
            "success": False,
            "error": f"old_string appears {count} times in {filepath}. Must be unique for safe replacement. Provide more context to make it unique."
        }

    # Perform replacement
    new_content = content.replace(old_string, new_string)

    # Write back
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "file": str(fpath),
            "message": f"Successfully replaced text in {filepath}",
        }
    except (OSError, IOError) as e:
        return {"success": False, "error": f"Cannot write file: {e}"}


def apply(patch_path: str, max_files: int = 5) -> dict:
    """
    Apply a unified diff patch file.

    Safety checks:
        - Patch file must exist
        - All target files must exist (no new file creation for safety)
        - Number of files touched must not exceed max_files

    Returns dict with:
        - success: bool
        - files_touched: list[str]
        - error: str (if failed)
    """
    ppath = Path(patch_path).resolve()

    if not ppath.exists():
        return {"success": False, "error": f"Patch file does not exist: {patch_path}"}

    try:
        with open(ppath, "r", encoding="utf-8") as f:
            patch_content = f.read()
    except (OSError, IOError) as e:
        return {"success": False, "error": f"Cannot read patch file: {e}"}

    # Parse patch to find affected files
    # Unified diff format: --- a/path or --- path
    file_pattern = re.compile(r"^---\s+(?:a/)?(.+?)(?:\t|$)", re.MULTILINE)
    files_in_patch = file_pattern.findall(patch_content)

    # Remove /dev/null entries (new files)
    files_in_patch = [f for f in files_in_patch if f != "/dev/null"]

    if not files_in_patch:
        return {"success": False, "error": "No valid files found in patch"}

    # Check file count limit
    if len(files_in_patch) > max_files:
        return {
            "success": False,
            "error": f"Patch touches {len(files_in_patch)} files, exceeds max_files_touched_per_run={max_files}",
            "files_in_patch": files_in_patch,
        }

    # Verify all target files exist
    missing_files = []
    for fpath in files_in_patch:
        if not Path(fpath).exists():
            missing_files.append(fpath)

    if missing_files:
        return {
            "success": False,
            "error": f"Target files do not exist: {missing_files}",
        }

    # Apply patch using system patch command
    try:
        result = subprocess.run(
            ["patch", "-p1", "--dry-run", "-i", str(ppath)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Dry-run failed: {result.stderr or result.stdout}",
            }

        # Dry run passed, apply for real
        result = subprocess.run(
            ["patch", "-p1", "-i", str(ppath)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Apply failed: {result.stderr or result.stdout}",
            }

    except FileNotFoundError:
        return {"success": False, "error": "patch command not found on system"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Patch command timed out"}

    return {
        "success": True,
        "files_touched": files_in_patch,
        "output": result.stdout,
    }


def run(cmd: str, timeout: int = 60, cwd: Optional[str] = None) -> dict:
    """
    Run a shell command and capture output.

    Returns dict with:
        - exit_code: int
        - stdout: str
        - stderr: str
        - command: str
    """
    work_dir = Path(cwd).resolve() if cwd else Path.cwd()

    if not work_dir.exists():
        return {"error": f"Working directory does not exist: {cwd}"}

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
        )

        return {
            "command": cmd,
            "cwd": str(work_dir),
            "exit_code": result.returncode,
            "stdout": result.stdout[:10000] if result.stdout else "",
            "stderr": result.stderr[:10000] if result.stderr else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "command": cmd,
            "cwd": str(work_dir),
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
        }
    except Exception as e:
        return {
            "command": cmd,
            "cwd": str(work_dir),
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
        }
