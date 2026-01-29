#!/usr/bin/env python3
"""
Interactive setup for VibeReps remote sync.
Prompts user for display name and creates account on server.
"""

import json
import secrets
import sys
import urllib.request
import urllib.error

from vibereps_config import (
    CONFIG_PATH,
    DEFAULT_API_URL,
    enable_remote_sync,
    get_remote_settings,
    load_config,
)


def generate_anonymous_name() -> str:
    """Generate an anonymous display name like 'anon_a3f2'."""
    return f"anon_{secrets.token_hex(2)}"


def validate_display_name(name: str) -> tuple[bool, str]:
    """Validate display name format.

    Returns (is_valid, error_message).
    """
    if not name:
        return False, "Display name cannot be empty"

    if len(name) < 3:
        return False, "Display name must be at least 3 characters"

    if len(name) > 20:
        return False, "Display name must be 20 characters or less"

    # Allow alphanumeric, underscore, hyphen
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if not all(c in allowed for c in name):
        return False, "Display name can only contain letters, numbers, underscores, and hyphens"

    return True, ""


def create_account(api_url: str, username: str) -> tuple[str, str] | None:
    """Create account on server.

    Returns (api_key, display_name) on success, None on failure.
    """
    try:
        url = f"{api_url.rstrip('/')}/api/users"
        data = json.dumps({"username": username}).encode()

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("api_key"), result.get("username")

    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"\nError: Display name '{username}' is already taken.")
            return None
        elif e.code == 422:
            print(f"\nError: Invalid display name format.")
            return None
        else:
            print(f"\nError: Server returned {e.code}: {e.reason}")
            return None
    except urllib.error.URLError as e:
        print(f"\nError: Could not connect to server: {e.reason}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"\nError: Invalid response from server")
        return None


def get_leaderboard_rank(api_url: str, api_key: str) -> int | None:
    """Get user's current leaderboard rank."""
    try:
        url = f"{api_url.rstrip('/')}/api/leaderboard"
        req = urllib.request.Request(url, headers={"X-API-Key": api_key})

        with urllib.request.urlopen(req, timeout=5) as resp:
            leaderboard = json.loads(resp.read().decode())
            # Find our rank (leaderboard is sorted by total_reps desc)
            return len(leaderboard) + 1  # New user is at the bottom

    except Exception:
        return None


def print_banner():
    """Print setup banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║             VibeReps Remote Sync Setup                    ║
╚═══════════════════════════════════════════════════════════╝
""")


def print_info():
    """Print info about remote sync."""
    print("""Remote sync lets you:
  • See your stats on the global leaderboard
  • Track your streak across devices
  • Compare with other Claude Code users

Your exercise data (reps, exercise type, timestamps) will be
sent to our server. Video/images NEVER leave your browser.
""")


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """Prompt for yes/no with default."""
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"{prompt} {suffix}: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")


def prompt_display_name() -> str:
    """Prompt for display name with validation."""
    print("""
Choose a display name for the leaderboard.
This is public - use something fun, not your real name.
Leave blank for anonymous (anon_XXXX).
""")

    while True:
        name = input("Display name: ").strip()

        if not name:
            name = generate_anonymous_name()
            print(f"Using anonymous name: {name}")
            return name

        valid, error = validate_display_name(name)
        if valid:
            return name

        print(f"  {error}. Try again.")


def run_setup(api_url: str = DEFAULT_API_URL):
    """Run interactive setup flow."""
    print_banner()

    # Check if already configured
    existing = get_remote_settings()
    if existing:
        config = load_config()
        display_name = config.get("remote_sync", {}).get("display_name", "unknown")
        print(f"Remote sync is already enabled as '{display_name}'.")
        if not prompt_yes_no("Reconfigure?", default=False):
            print("\nNo changes made.")
            return

    print_info()

    # Ask about enabling
    if not prompt_yes_no("Enable remote sync?", default=False):
        print("\nRemote sync not enabled. Your exercises are logged locally only.")
        print(f"Local log: ~/.vibereps/exercises.jsonl")
        print("\nRun this setup again anytime to enable remote sync.")
        return

    # Get display name
    display_name = prompt_display_name()

    # Create account
    print(f"\nCreating account on {api_url}...")
    result = create_account(api_url, display_name)

    if not result:
        print("\nSetup failed. Please try again or use a different display name.")
        return

    api_key, final_name = result

    # Save config
    if enable_remote_sync(api_url, api_key, final_name):
        print(f"""
Setup complete!

  Display name: {final_name}
  Config saved: {CONFIG_PATH}

Your exercises will now sync to the global leaderboard.
Start exercising with Claude Code to climb the ranks!
""")
    else:
        print(f"\nError: Could not save config to {CONFIG_PATH}")
        print(f"Your API key: {api_key}")
        print("You can manually set VIBEREPS_API_KEY environment variable.")


def run_non_interactive(api_url: str, display_name: str = ""):
    """Run setup non-interactively (for install.sh integration)."""
    # Generate anonymous name if not provided
    if not display_name.strip():
        display_name = generate_anonymous_name()

    # Validate if provided
    if display_name and not display_name.startswith("anon_"):
        valid, error = validate_display_name(display_name)
        if not valid:
            print(f"Error: {error}")
            return False

    # Create account
    print(f"Creating account as '{display_name}'...")
    result = create_account(api_url, display_name)

    if not result:
        return False

    api_key, final_name = result

    # Save config
    if enable_remote_sync(api_url, api_key, final_name):
        print(f"Remote sync enabled as '{final_name}'")
        return True
    else:
        print(f"Error: Could not save config")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="VibeReps remote sync setup")
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"API server URL (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current configuration status"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run non-interactively (for installer integration)"
    )
    parser.add_argument(
        "--display-name",
        default="",
        help="Display name for leaderboard (used with --non-interactive)"
    )

    args = parser.parse_args()

    if args.check:
        remote = get_remote_settings()
        if remote:
            config = load_config()
            name = config.get("remote_sync", {}).get("display_name", "unknown")
            print(f"Remote sync: enabled")
            print(f"Display name: {name}")
            print(f"Server: {remote[0]}")
        else:
            print("Remote sync: disabled")
            print("Run 'vibereps_setup.py' to enable")
        return

    if args.non_interactive:
        success = run_non_interactive(args.api_url, args.display_name)
        sys.exit(0 if success else 1)

    run_setup(api_url=args.api_url)


if __name__ == "__main__":
    main()
