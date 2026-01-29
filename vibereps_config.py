#!/usr/bin/env python3
"""
Configuration management for VibeReps.
Handles reading/writing ~/.vibereps/config.json with env var overrides.
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple

CONFIG_DIR = Path.home() / ".vibereps"
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_API_URL = "https://api.vibereps.com"  # TODO: Update when server is deployed

DEFAULT_CONFIG = {
    "version": 1,
    "local_logging": True,
    "remote_sync": {
        "enabled": False,
        "api_url": DEFAULT_API_URL,
        "api_key": None,
        "display_name": None
    }
}


def load_config() -> dict:
    """Load config from file, merging with defaults.

    Returns a config dict with all expected keys present.
    Missing keys are filled in from DEFAULT_CONFIG.
    """
    config = DEFAULT_CONFIG.copy()
    config["remote_sync"] = DEFAULT_CONFIG["remote_sync"].copy()

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                file_config = json.load(f)

            # Merge top-level keys
            for key in ["version", "local_logging"]:
                if key in file_config:
                    config[key] = file_config[key]

            # Merge remote_sync keys
            if "remote_sync" in file_config and isinstance(file_config["remote_sync"], dict):
                for key in ["enabled", "api_url", "api_key", "display_name"]:
                    if key in file_config["remote_sync"]:
                        config["remote_sync"][key] = file_config["remote_sync"][key]
        except (json.JSONDecodeError, OSError, KeyError):
            pass  # Use defaults on any error

    return config


def save_config(config: dict) -> bool:
    """Save config to file.

    Creates ~/.vibereps directory if needed.
    Sets file permissions to 0600 for security (contains API key).

    Returns True on success, False on failure.
    """
    try:
        CONFIG_DIR.mkdir(exist_ok=True)

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        # Secure permissions (owner read/write only)
        CONFIG_PATH.chmod(0o600)
        return True
    except OSError:
        return False


def get_remote_settings() -> Optional[Tuple[str, str]]:
    """Get remote sync settings if enabled.

    Environment variables override config file:
    - VIBEREPS_API_URL overrides config api_url
    - VIBEREPS_API_KEY overrides config api_key
    - If both env vars are set, remote sync is implicitly enabled

    Returns:
        (api_url, api_key) tuple if remote sync is enabled and configured
        None if remote sync is disabled or missing credentials
    """
    # Check environment variables first
    env_url = os.getenv("VIBEREPS_API_URL", "").strip()
    env_key = os.getenv("VIBEREPS_API_KEY", "").strip()

    # If both env vars are set, use them (implicit enable)
    if env_url and env_key:
        return (env_url, env_key)

    # Load config file
    config = load_config()
    remote = config.get("remote_sync", {})

    # Check if remote sync is enabled
    if not remote.get("enabled", False):
        return None

    # Get URL and key (env vars override config)
    api_url = env_url or remote.get("api_url") or DEFAULT_API_URL
    api_key = env_key or remote.get("api_key")

    if not api_key:
        return None

    return (api_url, api_key)


def is_local_logging_enabled() -> bool:
    """Check if local logging is enabled.

    Local logging is enabled by default and can be disabled in config.
    """
    config = load_config()
    return config.get("local_logging", True)


def get_display_name() -> Optional[str]:
    """Get the user's display name if configured."""
    config = load_config()
    return config.get("remote_sync", {}).get("display_name")


def enable_remote_sync(api_url: str, api_key: str, display_name: str) -> bool:
    """Enable remote sync with the given credentials.

    Saves the configuration to file.

    Returns True on success, False on failure.
    """
    config = load_config()
    config["remote_sync"] = {
        "enabled": True,
        "api_url": api_url,
        "api_key": api_key,
        "display_name": display_name
    }
    return save_config(config)


def disable_remote_sync() -> bool:
    """Disable remote sync (keeps credentials for potential re-enable).

    Returns True on success, False on failure.
    """
    config = load_config()
    config["remote_sync"]["enabled"] = False
    return save_config(config)


if __name__ == "__main__":
    # Simple test/debug output
    print(f"Config path: {CONFIG_PATH}")
    print(f"Config exists: {CONFIG_PATH.exists()}")
    print(f"Current config: {json.dumps(load_config(), indent=2)}")

    remote = get_remote_settings()
    if remote:
        print(f"Remote sync: enabled ({remote[0]})")
    else:
        print("Remote sync: disabled")
