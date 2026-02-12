#!/usr/bin/env python3
"""DEPRECATED: Use vibereps.py instead. This wrapper forwards to vibereps.py notification."""
import sys
import os
import subprocess

print("Warning: notify_complete.py is deprecated. Update hooks to use vibereps.py.", file=sys.stderr)
script_dir = os.path.dirname(os.path.abspath(__file__))
result = subprocess.run(
    [sys.executable, os.path.join(script_dir, "vibereps.py"), "notification"],
    stdin=sys.stdin,
)
sys.exit(result.returncode)
