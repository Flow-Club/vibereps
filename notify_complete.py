#!/usr/bin/env python3
"""
notify_complete.py - Notify exercise tracker when Claude completes
This script is triggered by the Notification hook
"""

import sys
import os
import json
import hashlib
import urllib.request
import urllib.error
import select
import time
from pathlib import Path


PORT_FILE = Path("/tmp/vibereps-port")
PORT_RANGE = range(8765, 8775)
ELECTRON_PORT = 8800  # Different from webapp's 8765-8774 range


def get_session_id_file(cwd: str = None):
    """Get the per-terminal session ID file path."""
    # Include cwd hash to differentiate multiple Claude instances in same parent
    cwd_hash = ""
    if cwd:
        cwd_hash = f"-{hashlib.md5(cwd.encode()).hexdigest()[:8]}"
    return Path(f"/tmp/vibereps-session-id-{os.getppid()}{cwd_hash}")


def read_hook_payload_from_stdin() -> dict:
    """Read Claude Code hook payload from stdin (non-blocking)."""
    if select.select([sys.stdin], [], [], 0.5)[0]:
        try:
            return json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def is_electron_app_running():
    """Check if the VibeReps Electron menubar app is running."""
    try:
        req = urllib.request.Request(
            f"http://localhost:{ELECTRON_PORT}/api/status",
            headers={"Accept": "application/json"}
        )
        response = urllib.request.urlopen(req, timeout=1)
        return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


def get_session_id(cwd: str = None):
    """Get the current session ID if available.

    First tries exact match (ppid + cwd hash), then falls back to
    searching for any session file with matching ppid in case
    the notification fires from a different directory than the
    original PostToolUse hook.
    """
    # Try exact match first
    session_id_file = get_session_id_file(cwd)
    if session_id_file.exists():
        try:
            return session_id_file.read_text().strip()
        except OSError:
            pass

    # Fallback: find any session file for this PPID
    # This handles cases where cwd differs between hooks
    ppid = os.getppid()
    for f in Path("/tmp").glob(f"vibereps-session-id-{ppid}*"):
        try:
            return f.read_text().strip()
        except OSError:
            continue

    return None


def notify_electron_app(notification_data: dict = None):
    """Send notification to Electron menubar app."""
    url = f"http://localhost:{ELECTRON_PORT}/api/notify"

    # Get cwd from notification data to find correct session ID
    cwd = notification_data.get("cwd") if notification_data else None
    payload = {"session_id": get_session_id(cwd)}
    if notification_data:
        payload["message"] = notification_data.get("message", "Claude finished!")
        payload["notification_type"] = notification_data.get("notification_type", "")

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            result = json.loads(response.read().decode())
            return {"status": "success", "message": "Electron app notified", "result": result}
    except (urllib.error.URLError, OSError) as e:
        return {"status": "error", "message": f"Failed to notify Electron app: {e}"}


def discover_port():
    """Find the port the exercise tracker is running on."""
    # Try port file first (fast path)
    if PORT_FILE.exists():
        try:
            port = int(PORT_FILE.read_text().strip())
            # Verify it's actually responding
            urllib.request.urlopen(f"http://localhost:{port}/status", timeout=0.5)
            return port
        except (ValueError, urllib.error.URLError, OSError):
            pass

    # Scan port range (slower fallback)
    for port in PORT_RANGE:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/status", timeout=0.3)
            return port
        except (urllib.error.URLError, OSError):
            continue

    return None


def notify_exercise_tracker(notification_data: dict = None, max_retries=3):
    """Send notification to exercise tracker that Claude is done."""
    # Discover port
    port = discover_port()
    if not port:
        return {"status": "skipped", "message": "Exercise tracker not running"}

    url = f"http://localhost:{port}/notify"

    # Include notification message if available
    payload = {}
    if notification_data:
        payload["message"] = notification_data.get("message", "")
        payload["notification_type"] = notification_data.get("notification_type", "")

    # Retry with exponential backoff
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=2) as response:
                result = json.loads(response.read().decode())
                return {"status": "success", "message": "Exercise tracker notified", "result": result}

        except urllib.error.URLError as e:
            if "Connection refused" in str(e):
                # Server definitely not running
                return {"status": "skipped", "message": "Exercise tracker not running"}
            # Transient error - retry
            if attempt < max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))  # 0.1s, 0.2s, 0.4s
                continue
            return {"status": "error", "message": f"Notification failed after {max_retries} attempts: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Notification failed: {e}"}

    return {"status": "error", "message": "Notification failed"}


def main():
    # Read hook payload from stdin (Claude Code passes data there)
    hook_data = read_hook_payload_from_stdin()

    # First try Electron menubar app
    if is_electron_app_running():
        result = notify_electron_app(hook_data)
        if result["status"] == "success":
            # Check if notification actually showed
            # If Electron is running but notifications aren't supported,
            # fall through to browser tracker as backup
            if result.get("result", {}).get("notification_shown", True):
                print(json.dumps(result))
                return 0
            # Fall through to browser tracker
        else:
            print(json.dumps(result))
            return 1

    # Fall back to legacy browser-based tracker
    result = notify_exercise_tracker(hook_data)

    # Output result for hook logging
    print(json.dumps(result))

    return 0 if result["status"] in ["success", "skipped"] else 1


if __name__ == "__main__":
    sys.exit(main())
