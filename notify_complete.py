#!/usr/bin/env python3
"""
notify_complete.py - Notify exercise tracker when Claude completes
This script is triggered by the Notification hook
"""

import sys
import json
import urllib.request
import urllib.error
import select
import time
from pathlib import Path


PORT_FILE = Path("/tmp/vibereps-port")
PORT_RANGE = range(8765, 8775)


def read_hook_payload_from_stdin() -> dict:
    """Read Claude Code hook payload from stdin (non-blocking)."""
    if select.select([sys.stdin], [], [], 0.1)[0]:
        try:
            return json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


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

    # Send notification with any available data
    result = notify_exercise_tracker(hook_data)

    # Output result for hook logging
    print(json.dumps(result))

    return 0 if result["status"] in ["success", "skipped"] else 1


if __name__ == "__main__":
    sys.exit(main())
