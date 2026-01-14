#!/usr/bin/env python3
"""
notify_complete.py - Notify exercise tracker when Claude completes
This script is triggered by the PostMessage hook
"""

import sys
import json
import urllib.request
import urllib.error

def notify_exercise_tracker(port=8765):
    """Send notification to exercise tracker that Claude is done"""
    url = f"http://localhost:{port}/notify"

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({}).encode('utf-8'),
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
    # Can receive event data from hook, but we don't need it for this simple case
    if len(sys.argv) > 1:
        event_data = json.loads(sys.argv[1]) if sys.argv[1] != '{}' else {}
    else:
        event_data = {}

    # Send notification
    result = notify_exercise_tracker()

    # Output result for hook logging
    print(json.dumps(result))

    return 0 if result["status"] in ["success", "skipped"] else 1

if __name__ == "__main__":
    sys.exit(main())
