"""Configuration loader for Cappy Code."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, List

import yaml


@dataclass
class CappyConfig:
    """Type-safe configuration for Cappy Code."""
    
    # Model settings
    default_model: str = "o1"
    allowed_models: List[str] = field(default_factory=lambda: ["gpt-4.1", "o1", "gemini25pro"])
    
    # Limits
    max_files_touched_per_run: int = 5
    max_iterations: int = 20
    max_tool_calls_per_session: int = 50
    max_search_results: int = 50
    
    # Timeouts (seconds)
    api_timeout: int = 120
    default_command_timeout: int = 60
    
    # Retry settings
    api_retry_attempts: int = 3
    api_retry_backoff: float = 2.0
    
    # Safety
    require_plan: bool = True
    verify_command: Optional[str] = None
    block_dangerous_commands: bool = True
    
    # Paths
    log_dir: str = "./logs"
    conversation_dir: str = "./conversations"
    
    # Undo
    auto_snapshot: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.max_files_touched_per_run < 1:
            errors.append("max_files_touched_per_run must be >= 1")
        
        if self.max_iterations < 1:
            errors.append("max_iterations must be >= 1")
        
        if self.api_timeout < 10:
            errors.append("api_timeout must be >= 10 seconds")
        
        if self.api_retry_attempts < 0:
            errors.append("api_retry_attempts must be >= 0")
        
        if self.api_retry_backoff < 1.0:
            errors.append("api_retry_backoff must be >= 1.0")
        
        if not self.allowed_models:
            errors.append("allowed_models cannot be empty")
        
        return errors


DEFAULT_CONFIG = {
    "allowed_models": ["gpt-4.1"],
    "max_files_touched_per_run": 5,
    "require_plan": True,
    "verify_command": None,
    "log_dir": "./logs",
}

CONFIG_FILENAME = "cappy_config.yaml"


def find_config_file(start_path: str = ".") -> Optional[Path]:
    """
    Search for cappy_config.yaml starting from start_path and walking up.

    Returns the path to the config file, or None if not found.
    """
    current = Path(start_path).resolve()

    for _ in range(20):  # Max depth to prevent infinite loop
        config_path = current / CONFIG_FILENAME
        if config_path.exists():
            return config_path

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return None


def load_config(config_path: Optional[str] = None) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Explicit path to config file. If None, searches for it.

    Returns:
        Merged config dict (defaults + file overrides)
    """
    config = DEFAULT_CONFIG.copy()

    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()

    if path and path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
            config.update(file_config)
            config["_config_file"] = str(path)
        except (yaml.YAMLError, OSError) as e:
            config["_config_error"] = str(e)
    else:
        config["_config_file"] = None

    return config


# Cached config instance
_config: Optional[dict[str, Any]] = None


def get_config(reload: bool = False) -> dict[str, Any]:
    """Get the cached config, loading if necessary."""
    global _config
    if _config is None or reload:
        _config = load_config()
    return _config


def get_typed_config(reload: bool = False) -> CappyConfig:
    """Get type-safe config object."""
    config_dict = get_config(reload=reload)
    
    # Extract only fields that match CappyConfig
    config_obj = CappyConfig()
    for key in config_obj.__dataclass_fields__:
        if key in config_dict:
            setattr(config_obj, key, config_dict[key])
    
    return config_obj


def validate_config(config_path: Optional[str] = None) -> tuple[bool, List[str]]:
    """Validate configuration file and return (is_valid, errors)."""
    try:
        config_dict = load_config(config_path)
        
        # Check for YAML errors
        if "_config_error" in config_dict:
            return False, [f"YAML error: {config_dict['_config_error']}"]
        
        # Create typed config and validate
        config_obj = CappyConfig()
        for key in config_obj.__dataclass_fields__:
            if key in config_dict:
                setattr(config_obj, key, config_dict[key])
        
        errors = config_obj.validate()
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Validation error: {e}"]
