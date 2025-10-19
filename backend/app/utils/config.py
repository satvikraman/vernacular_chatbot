import os
import json
from pathlib import Path
from app.utils.env import is_local  # your helper to detect LOCAL environment

# Cache the loaded config to avoid re-reading the file multiple times
_config_cache = {}

def _load_config():
    """Load and merge base config and local config if in LOCAL environment."""
    global _config_cache
    if _config_cache:
        return _config_cache  # return cached copy

    # Determine paths
    project_root = Path(__file__).parent.parent  # assumes utils/ is inside app/
    base_config_path = project_root / "config.json"
    local_config_path = project_root / "config.local.json"

    # Load base config
    config = {}
    if base_config_path.exists():
        with open(base_config_path, "r") as f:
            config = json.load(f)

    # Override with local config if ENVIRONMENT=LOCAL
    if is_local() and local_config_path.exists():
        with open(local_config_path, "r") as f:
            local_config = json.load(f)
            config.update(local_config)  # local overrides base

    _config_cache = config
    return config

def get_config(key, default=None):
    """Get the value of a config parameter."""
    config = _load_config()
    return config.get(key, default)
