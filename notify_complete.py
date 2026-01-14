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


def read_hook_payload_from_stdin() -> dict:
    """Read Claude Code hook payload from stdin (non-blocking)."""
    if select.select([sys.stdin], [], [], 0.1)[0]:
        try:
            return json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def notify_exercise_tracker(notification_data: dict = None, port=8765):
    """Send notification to exercise tracker that Claude is done"""
    url = f"http://localhost:{port}/notify"

    # Include notification message if available
    payload = {}
    if notification_data:
        payload["message"] = notification_data.get("message", "")
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
            return {"status": "success", "message": "Exercise tracker notified", "result": result}

    except urllib.error.URLError as e:
        # Exercise tracker might not be running - that's OK
        return {"status": "skipped", "message": f"Exercise tracker not running: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Notification failed: {e}"}


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
