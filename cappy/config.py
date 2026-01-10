"""Configuration loader for Cappy Code."""

from pathlib import Path
from typing import Any, Optional

import yaml


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
