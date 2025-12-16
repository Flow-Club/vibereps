#!/usr/bin/env python3
"""
Claude Code hook to track which projects/branches are being worked on.

This hook sends metrics to Prometheus Pushgateway when Claude Code sessions
interact with different projects and git branches.

Usage:
  Add to ~/.claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [
        {
          "type": "command",
          "command": "/path/to/track_project.py"
        }
      ]
    }
  }

Metrics exported:
  - claude_project_session_total: Counter of sessions per project/branch
  - claude_project_active: Gauge showing currently active project (1 = active)
"""

import os
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")


def get_git_info():
    """Get current git branch and remote info."""
    try:
        # Get current branch
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        branch_name = branch.stdout.strip() if branch.returncode == 0 else "unknown"

        # Get repo name from remote or directory
        remote = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if remote.returncode == 0 and remote.stdout.strip():
            # Extract repo name from URL like git@github.com:user/repo.git
            url = remote.stdout.strip()
            repo_name = url.split("/")[-1].replace(".git", "")
        else:
            # Fall back to directory name
            repo_name = Path.cwd().name

        return branch_name, repo_name
    except Exception:
        return "unknown", Path.cwd().name


def get_project_name():
    """Get project name from directory."""
    return Path.cwd().name


def push_metrics(project: str, branch: str):
    """Push metrics to Prometheus Pushgateway."""
    # Sanitize labels (remove special characters)
    project = "".join(c if c.isalnum() or c in "-_" else "_" for c in project)
    branch = "".join(c if c.isalnum() or c in "-_" else "_" for c in branch)

    metrics = f"""# HELP claude_project_session_total Total sessions per project and branch
# TYPE claude_project_session_total counter
claude_project_session_total{{project="{project}",branch="{branch}"}} 1
# HELP claude_project_active Currently active project
# TYPE claude_project_active gauge
claude_project_active{{project="{project}",branch="{branch}"}} 1
# HELP claude_project_last_active_timestamp Last activity timestamp
# TYPE claude_project_last_active_timestamp gauge
claude_project_last_active_timestamp{{project="{project}",branch="{branch}"}} {datetime.now().timestamp()}
"""

    # Push to pushgateway
    job_name = "claude_project_tracker"
    url = f"{PUSHGATEWAY_URL}/metrics/job/{job_name}/project/{project}/branch/{branch}"

    try:
        req = urllib.request.Request(
            url,
            data=metrics.encode("utf-8"),
            method="POST"
        )
        req.add_header("Content-Type", "text/plain")
        with urllib.request.urlopen(req, timeout=5) as response:
            pass  # Success
    except urllib.error.URLError:
        # Pushgateway not available, silently ignore
        pass
    except Exception:
        pass


def main():
    branch, repo = get_git_info()
    project = get_project_name()

    # Use repo name if available, otherwise directory name
    project_name = repo if repo != "unknown" else project

    push_metrics(project_name, branch)


if __name__ == "__main__":
    main()
