"""Undo functionality using git for Cappy Code."""

import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class UndoManager:
    """Manages undo/redo using git stash."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self._ensure_git_repo()
    
    def _ensure_git_repo(self):
        """Ensure we're in a git repo, initialize if not."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=True,
                )
                # Create initial commit
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.repo_path,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit (Cappy)", "--allow-empty"],
                    cwd=self.repo_path,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Git not available or failed, silently continue
                pass
    
    def snapshot(self, message: str = "Cappy snapshot") -> bool:
        """Create a snapshot of current state."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            
            # Create stash with message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"{message} ({timestamp})"
            
            result = subprocess.run(
                ["git", "stash", "push", "-m", full_message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            return result.returncode == 0
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def undo(self) -> tuple[bool, str]:
        """Undo last change by popping stash."""
        try:
            result = subprocess.run(
                ["git", "stash", "pop"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, "Undo successful"
            
        except subprocess.CalledProcessError as e:
            return False, f"Undo failed: {e.stderr if e.stderr else 'No snapshots available'}"
        except FileNotFoundError:
            return False, "Git not available"
    
    def list_snapshots(self) -> List[dict]:
        """List available snapshots."""
        try:
            result = subprocess.run(
                ["git", "stash", "list"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            
            snapshots = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                # Parse: stash@{0}: On main: message (timestamp)
                parts = line.split(": ", 2)
                if len(parts) >= 3:
                    snapshots.append({
                        "ref": parts[0],
                        "message": parts[2],
                    })
            
            return snapshots
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
    
    def clear_snapshots(self) -> bool:
        """Clear all snapshots."""
        try:
            subprocess.run(
                ["git", "stash", "clear"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


# Global undo manager
_undo_manager: Optional[UndoManager] = None


def get_undo_manager() -> UndoManager:
    """Get or create global undo manager."""
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoManager()
    return _undo_manager
