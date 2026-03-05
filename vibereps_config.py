"""Centralized configuration module for vibereps.

Provides load/save for ~/.vibereps/config.json with:
- Secure file permissions (0o600) since config may contain API keys
- Environment variable overrides for remote settings
- Pause state management
"""

import json
import os
from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path.home() / ".vibereps"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load config from ~/.vibereps/config.json. Returns empty dict if missing."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_config(config: dict) -> bool:
    """Write config to ~/.vibereps/config.json with secure permissions."""
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        try:
            CONFIG_FILE.chmod(0o600)
        except OSError:
            pass  # Best-effort on systems that don't support chmod
        return True
    except OSError:
        return False


def get_remote_settings() -> dict:
    """Get remote server settings. Env vars override config file values."""
    config = load_config()
    remote = config.get("remote_sync", {})
    return {
        "api_url": os.getenv("VIBEREPS_API_URL", remote.get("api_url", "")),
        "api_key": os.getenv("VIBEREPS_API_KEY", remote.get("api_key", "")),
    }


def is_paused() -> bool:
    """Check if vibereps is paused (paused_until timestamp in config)."""
    config = load_config()
    paused_until = config.get("paused_until")
    if not paused_until:
        return False
    try:
        pause_time = datetime.fromisoformat(paused_until.replace("Z", "+00:00"))
        now = datetime.now()
        if pause_time.tzinfo:
            now = datetime.now(pause_time.tzinfo)
        return now < pause_time
    except (ValueError, TypeError):
        return False


def get_paused_until() -> str | None:
    """Get the paused_until timestamp string, or None if not set."""
    return load_config().get("paused_until")


def set_pause(until_timestamp: str) -> bool:
    """Set pause until a specific timestamp."""
    config = load_config()
    config["paused_until"] = until_timestamp
    return save_config(config)


def clear_pause() -> bool:
    """Clear the pause state."""
    config = load_config()
    config.pop("paused_until", None)
    return save_config(config)
