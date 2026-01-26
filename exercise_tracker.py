#!/usr/bin/env python3
"""
exercise_tracker.py - Claude Code hook for exercise tracking
Launches exercise UI when Claude edits code. Keeps you moving until Claude finishes.
"""

import sys
import json
import webbrowser
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.error

# Electron app port (different from webapp's 8765-8774 range)
ELECTRON_PORT = 8800
ELECTRON_APP_PATH = "/Applications/VibeReps.app"


def launch_electron_app() -> bool:
    """Try to launch the Electron app if installed. Returns True if app started successfully."""
    if not os.path.exists(ELECTRON_APP_PATH):
        return False

    # Use lock file to prevent multiple simultaneous launch attempts
    lock_file = Path("/tmp/vibereps-electron-launch.lock")
    try:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        # Another process is launching, check if stale (> 15s)
        try:
            if time.time() - lock_file.stat().st_mtime < 15:
                # Wait for other process to finish launching
                for _ in range(10):
                    time.sleep(0.5)
                    if is_electron_app_running():
                        return True
                return False
            lock_file.unlink(missing_ok=True)
        except (OSError, FileNotFoundError):
            pass
        return False

    try:
        subprocess.Popen(
            ["open", ELECTRON_APP_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Wait for app to start (check port directly to avoid circular dependency)
        for _ in range(10):
            time.sleep(0.5)
            try:
                req = urllib.request.Request(
                    f"http://localhost:{ELECTRON_PORT}/api/status",
                    headers={"Accept": "application/json"}
                )
                response = urllib.request.urlopen(req, timeout=1)
                if response.status == 200:
                    lock_file.unlink(missing_ok=True)
                    return True
            except (urllib.error.URLError, OSError):
                continue
        lock_file.unlink(missing_ok=True)
        return False
    except Exception:
        lock_file.unlink(missing_ok=True)
        return False


# Handle --list-exercises before anything else
if len(sys.argv) > 1 and sys.argv[1] in ("--list-exercises", "-l"):
    exercises_dir = Path(__file__).parent / "exercises"
    print("Available exercises:\n")
    for json_file in sorted(exercises_dir.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        try:
            content = json.loads(json_file.read_text())
            name = content.get("name", json_file.stem)
            desc = content.get("description", "")
            quick_reps = content.get("reps", {}).get("quick", 5)
            print(f"  {json_file.stem:20} {name} ({quick_reps} reps)")
            if desc:
                print(f"  {' '*20} {desc[:60]}")
        except (json.JSONDecodeError, KeyError):
            continue
    print("\nSet VIBEREPS_EXERCISES to choose exercises:")
    print("  export VIBEREPS_EXERCISES=squats,jumping_jacks,calf_raises")
    sys.exit(0)

# Handle --help
if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
    print("""VibeReps Exercise Tracker

Usage:
  exercise_tracker.py [event_type] [data]    Run as Claude Code hook
  exercise_tracker.py --list-exercises       List available exercises
  exercise_tracker.py --help                 Show this help

Event types:
  post_tool_use     Quick mode (5 reps while Claude works)
  user_prompt_submit Quick mode (5 reps while Claude works)
  task_complete     Normal mode (10 reps after Claude finishes)

Environment variables:
  VIBEREPS_EXERCISES     Comma-separated list of exercises to use
  VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY  Set to 1 to --dangerously-skip-leg-day
  VIBEREPS_DISABLED      Set to 1 to disable tracking
  VIBEREPS_API_URL       Remote server URL for logging
  VIBEREPS_API_KEY       API key for remote server
""")
    sys.exit(0)

# Quick disable - set VIBEREPS_DISABLED=1 to skip exercise tracking
if os.getenv("VIBEREPS_DISABLED", ""):
    print('{"status": "skipped", "message": "VIBEREPS_DISABLED is set"}')
    sys.exit(0)

# Configuration - set these environment variables or edit directly
VIBEREPS_API_URL = os.getenv("VIBEREPS_API_URL", "")  # e.g., "https://vibereps.example.com"
VIBEREPS_API_KEY = os.getenv("VIBEREPS_API_KEY", "")  # Your API key
VIBEREPS_EXERCISES = os.getenv("VIBEREPS_EXERCISES", "")  # Comma-separated: "squats,pushups,jumping_jacks"
VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY = os.getenv("VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY", "")  # Set to 1 to --dangerously-skip-leg-day

# Electron app port (fixed port for the menubar app, outside webapp's 8765-8774 range)
ELECTRON_PORT = 8800

# Exercises that require legs (filtered out when VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY=1)
LEG_EXERCISES = {"squats", "calf_raises", "high_knees", "jumping_jacks"}


def get_filtered_exercises():
    """Get exercise list, filtering out leg exercises if skip-leg-day is enabled."""
    exercises = VIBEREPS_EXERCISES
    if VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY and exercises:
        exercise_list = [e.strip() for e in exercises.split(",")]
        exercise_list = [e for e in exercise_list if e not in LEG_EXERCISES]
        exercises = ",".join(exercise_list)
    return exercises


# Action words that suggest a prompt will result in code edits
EDIT_ACTION_WORDS = {
    # Direct edit commands
    "fix", "add", "update", "change", "implement", "create", "write", "make",
    "modify", "edit", "refactor", "rename", "move", "delete", "remove",
    "replace", "insert", "append", "prepend",
    # Feature/task words
    "build", "develop", "code", "program", "script",
    "feature", "function", "method", "class", "component",
    # Bug/issue words
    "bug", "error", "issue", "problem", "broken",
    # Improvement words
    "improve", "optimize", "enhance", "upgrade", "migrate",
    # Integration words
    "integrate", "connect", "hook", "wire", "link",
    # Test words (often involve writing code)
    "test", "spec",
}

# Words that suggest the prompt is just a question (skip exercise)
QUESTION_WORDS = {
    "what", "why", "how", "where", "when", "which", "who",
    "explain", "describe", "tell", "show", "list", "find",
    "search", "look", "check", "verify", "confirm",
    "understand", "learn", "help", "?",
}


def prompt_likely_to_edit(prompt: str) -> bool:
    """
    Analyze a prompt to guess if it will result in code edits.
    Returns True if we think edits are likely, False otherwise.
    """
    if not prompt:
        return False

    prompt_lower = prompt.lower().strip()
    words = set(prompt_lower.split())

    # Check for explicit action words (strong signals for editing)
    strong_action_words = {
        "fix", "add", "update", "change", "implement", "create", "write", "make",
        "modify", "edit", "refactor", "rename", "delete", "remove", "replace",
        "build", "develop", "integrate", "migrate", "improve", "optimize",
    }
    has_strong_action = bool(words & strong_action_words)

    # Check if it starts with a question word (strong signal for NOT editing)
    first_word = prompt_lower.split()[0] if prompt_lower else ""
    starts_with_question = first_word in {"what", "why", "how", "where", "when", "which", "who", "does", "is", "are", "can", "could", "would", "should"}

    # Check if it's primarily a question
    is_question = prompt_lower.endswith("?")

    # If it starts with a question word and ends with ?, it's likely just a question
    if starts_with_question and is_question and not has_strong_action:
        return False

    # If it starts with a question word but has strong action words, might be a request
    # e.g., "Can you fix this?" or "Could you add a button?"
    if starts_with_question and has_strong_action:
        return True

    # If it has strong action words, likely to edit
    if has_strong_action:
        return True

    # Check for imperative patterns (commands)
    imperative_starts = ["let's", "lets", "please", "go ahead", "now"]
    for pattern in imperative_starts:
        if prompt_lower.startswith(pattern):
            return True

    # Check for request patterns with action context
    request_patterns = ["i want", "i need", "we need", "we should", "i'd like"]
    for pattern in request_patterns:
        if pattern in prompt_lower:
            return True

    # Default: if it's a question, probably not editing
    if is_question or starts_with_question:
        return False

    return False



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


def generate_session_id():
    """Generate a unique session ID based on terminal PID and timestamp."""
    ppid = os.getppid()  # Parent process (Claude Code's shell)
    timestamp = int(time.time() * 1000)
    return f"session-{ppid}-{timestamp}"


def register_with_electron_app(session_id: str, context: dict):
    """Register a new session with the Electron menubar app."""
    try:
        data = json.dumps({
            "session_id": session_id,
            "pid": os.getpid(),
            "context": context
        }).encode('utf-8')

        req = urllib.request.Request(
            f"http://localhost:{ELECTRON_PORT}/api/session/register",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )
        response = urllib.request.urlopen(req, timeout=2)
        result = json.loads(response.read().decode('utf-8'))
        return result.get("success", False)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        print(f"Failed to register with Electron app: {e}", file=sys.stderr)
        return False


def report_activity_to_electron(session_id: str, tool_name: str, file_path: str = None):
    """Report activity (tool use) to the Electron app."""
    try:
        data = json.dumps({
            "session_id": session_id,
            "tool_name": tool_name,
            "file_path": file_path
        }).encode('utf-8')

        req = urllib.request.Request(
            f"http://localhost:{ELECTRON_PORT}/api/session/activity",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )
        urllib.request.urlopen(req, timeout=1)
        return True
    except (urllib.error.URLError, OSError):
        return False


def is_vibereps_window_open():
    """Check if a vibereps Chrome window is already open."""
    import platform
    system = platform.system()

    if system == "Darwin":  # macOS
        try:
            # Check if Chrome process exists with vibereps user data dir
            result = subprocess.run(
                ["pgrep", "-f", "vibereps-chrome"],
                capture_output=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            pass
    elif system == "Linux":
        try:
            result = subprocess.run(
                ["pgrep", "-f", "vibereps-chrome"],
                capture_output=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            pass

    return False


def open_small_window(url: str, width: int = 340, height: int = 700):
    """Open URL in a small browser window (Chrome app mode preferred)."""
    import platform
    import shutil

    # Check if window already exists
    if is_vibereps_window_open():
        return  # Don't open duplicate window

    system = platform.system()

    # Try Chrome first (best small window experience with --app mode)
    chrome_paths = []
    if system == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Linux":
        chrome_paths = [shutil.which("google-chrome"), shutil.which("chromium")]
    elif system == "Windows":
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        ]

    for chrome in chrome_paths:
        if chrome and os.path.exists(chrome):
            try:
                subprocess.Popen([
                    chrome,
                    f"--app={url}",
                    f"--window-size={width},{height}",
                    "--window-position=50,50",
                    "--user-data-dir=/tmp/vibereps-chrome",
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                continue

    # Fallback to default browser
    webbrowser.open(url)


def log_to_local(exercise: str, reps: int, duration: int = 0, mode: str = "normal") -> bool:
    """Log exercise data to local JSONL file for ccusage integration."""
    from datetime import datetime

    log_dir = Path.home() / ".vibereps"
    log_file = log_dir / "exercises.jsonl"

    try:
        log_dir.mkdir(exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "exercise": exercise,
            "reps": reps,
            "duration": duration,
            "mode": mode
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return True
    except Exception:
        return False


def log_to_remote(exercise: str, reps: int, duration: int = 0) -> bool:
    """Send exercise data to remote VibeReps server."""
    if not VIBEREPS_API_URL or not VIBEREPS_API_KEY:
        return False  # Remote logging disabled

    try:
        url = f"{VIBEREPS_API_URL.rstrip('/')}/api/log"
        data = json.dumps({"exercise": exercise, "reps": reps, "duration": duration}).encode()

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": VIBEREPS_API_KEY
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200

    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Warning: Failed to log to remote server: {e}")
        return False


def extract_context_from_hook(hook_data: dict) -> dict:
    """Extract useful context from Claude Code hook payload."""
    context = {
        "source": "hook",
        "tool_name": hook_data.get("tool_name"),
        "hook_event": hook_data.get("hook_event_name"),
        "cwd": hook_data.get("cwd"),
        "files_modified": [],
        "summary": None,
        "recent_activity": []
    }

    # Extract file info from tool_input
    tool_input = hook_data.get("tool_input", {})
    if isinstance(tool_input, dict):
        file_path = tool_input.get("file_path") or tool_input.get("path")
        if file_path:
            # Get just the filename for display
            context["files_modified"].append(Path(file_path).name)
            context["summary"] = f"Edited {Path(file_path).name}"

        # For Bash tool, show the command
        command = tool_input.get("command")
        if command and context["tool_name"] == "Bash":
            # Truncate long commands
            cmd_display = command[:50] + "..." if len(command) > 50 else command
            context["summary"] = f"Ran: {cmd_display}"

    return context


def parse_transcript_for_context(transcript_path: str, max_entries: int = 5) -> list:
    """Parse Claude Code transcript file to get recent activity."""
    recent_activity = []

    if not transcript_path or not Path(transcript_path).exists():
        return recent_activity

    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()

        # Parse last N lines (JSONL format)
        for line in lines[-max_entries * 3:]:  # Read extra to account for non-tool entries
            try:
                entry = json.loads(line.strip())

                # Look for tool use entries
                if entry.get("type") == "tool_use":
                    tool_name = entry.get("name", "unknown")
                    tool_input = entry.get("input", {})

                    activity = {"tool": tool_name}

                    # Extract relevant info based on tool type
                    if tool_name in ("Write", "Edit"):
                        file_path = tool_input.get("file_path", "")
                        activity["description"] = f"Edited {Path(file_path).name}" if file_path else "Edited file"
                    elif tool_name == "Bash":
                        cmd = tool_input.get("command", "")[:40]
                        activity["description"] = f"Ran: {cmd}"
                    elif tool_name == "Read":
                        file_path = tool_input.get("file_path", "")
                        activity["description"] = f"Read {Path(file_path).name}" if file_path else "Read file"
                    elif tool_name in ("Glob", "Grep"):
                        pattern = tool_input.get("pattern", "")[:30]
                        activity["description"] = f"Searched: {pattern}"
                    else:
                        activity["description"] = f"Used {tool_name}"

                    recent_activity.append(activity)

                # Look for assistant messages to understand intent
                elif entry.get("type") == "assistant" and entry.get("message"):
                    msg = entry.get("message", {})
                    if isinstance(msg, dict):
                        content = msg.get("content", "")
                        if isinstance(content, str) and len(content) > 10:
                            # First 100 chars of what Claude said
                            recent_activity.append({
                                "tool": "thinking",
                                "description": content[:100] + "..." if len(content) > 100 else content
                            })

            except json.JSONDecodeError:
                continue

        # Return most recent entries
        return recent_activity[-max_entries:]

    except Exception:
        return recent_activity


def build_claude_context(hook_data: dict) -> dict:
    """Build complete context from hook payload and transcript."""
    context = extract_context_from_hook(hook_data)

    # Add transcript context if available
    transcript_path = hook_data.get("transcript_path")
    if transcript_path:
        context["recent_activity"] = parse_transcript_for_context(transcript_path)

    return context


class ExerciseHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler to serve the exercise UI and handle completion"""

    exercise_complete = False
    completion_data = {}
    claude_complete = False
    quick_mode = False
    claude_sessions = {}  # {session_id: {context: {...}, last_seen: timestamp}}
    tracker = None  # Reference to ExerciseTrackerHook for shutdown coordination
    SESSION_TIMEOUT = 1800  # 30 minutes - remove stale sessions
    COMPLETED_SESSION_TIMEOUT = 120  # 2 minutes - remove completed sessions faster

    def do_GET(self):
        """Serve the exercise tracker HTML and exercise definitions"""
        # Parse path without query parameters
        from urllib.parse import urlparse
        parsed_path = urlparse(self.path).path

        if parsed_path == '/' or parsed_path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            html_content = self.get_exercise_interface()
            self.wfile.write(html_content.encode('utf-8'))
        elif parsed_path == '/status':
            # Check if Claude is done
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "claude_complete": ExerciseHTTPHandler.claude_complete,
                "exercise_complete": ExerciseHTTPHandler.exercise_complete
            }
            self.wfile.write(json.dumps(status).encode())
        elif parsed_path == '/exercises':
            # List all exercise definitions
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            exercises = self.get_exercise_list()
            self.wfile.write(json.dumps(exercises).encode())
        elif parsed_path.startswith('/exercises/') and parsed_path.endswith('.json'):
            # Serve individual exercise file
            filename = parsed_path.split('/')[-1]
            exercise_content = self.get_exercise_file(filename)

            if exercise_content:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(exercise_content.encode())
            else:
                self.send_error(404, f"Exercise file not found: {filename}")
        elif parsed_path == '/context':
            # Serve aggregated Claude context from all sessions
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Clean up stale sessions
            self._cleanup_stale_sessions()

            # Aggregate context from all active sessions
            aggregated = self._aggregate_sessions()
            self.wfile.write(json.dumps(aggregated).encode())
        elif parsed_path.startswith('/assets/'):
            # Serve static assets (favicon, icons)
            asset_content = self.get_asset_file(parsed_path[8:])  # Remove '/assets/' prefix
            if asset_content:
                self.send_response(200)
                content_type = self._get_content_type(parsed_path)
                self.send_header('Content-type', content_type)
                self.send_header('Cache-Control', 'max-age=86400')  # Cache for 1 day
                self.end_headers()
                self.wfile.write(asset_content)
            else:
                self.send_error(404, f"Asset not found: {parsed_path}")
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle completion callback"""
        if self.path == '/complete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode())
                ExerciseHTTPHandler.completion_data = data
                ExerciseHTTPHandler.exercise_complete = True

                # Log to remote server if configured
                exercise = data.get("exercise", "unknown")
                reps = data.get("reps", 0)
                duration = data.get("duration", 0)
                mode = "quick" if ExerciseHTTPHandler.quick_mode else "normal"

                # Don't log internal states like _standup_check
                local_logged = False
                remote_logged = False
                if exercise and not exercise.startswith("_") and reps > 0:
                    local_logged = log_to_local(exercise, reps, duration, mode)
                    remote_logged = log_to_remote(exercise, reps, duration)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "local_logged": local_logged,
                    "remote_logged": remote_logged
                }).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/update-context':
            # Update context for a specific Claude session
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    session_id = data.get("session_id", "default")
                    context = data.get("context", {})

                    ExerciseHTTPHandler.claude_sessions[session_id] = {
                        "context": context,
                        "last_seen": time.time()
                    }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "updated"}).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/notify':
            # Notification from Claude that it's done
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    notify_data = json.loads(post_data.decode())
                    session_id = notify_data.get("session_id", "default")

                    # Update the session with notification info
                    if session_id in ExerciseHTTPHandler.claude_sessions:
                        if notify_data.get("message"):
                            ExerciseHTTPHandler.claude_sessions[session_id]["context"]["notification"] = notify_data.get("message")
                            ExerciseHTTPHandler.claude_sessions[session_id]["context"]["notification_type"] = notify_data.get("notification_type")
                        ExerciseHTTPHandler.claude_sessions[session_id]["context"]["complete"] = True

                ExerciseHTTPHandler.claude_complete = True

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "notified"}).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/shutdown':
            # Clean shutdown requested by browser
            try:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "shutting_down"}).encode())

                # Signal shutdown to the tracker
                if hasattr(ExerciseHTTPHandler, 'tracker') and ExerciseHTTPHandler.tracker:
                    ExerciseHTTPHandler.tracker.shutdown_requested = True
            except Exception:
                pass  # May fail if connection closed
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """Suppress server logs"""
        pass

    def _cleanup_stale_sessions(self):
        """Remove sessions that haven't been updated recently"""
        now = time.time()
        stale_ids = []
        for sid, data in ExerciseHTTPHandler.claude_sessions.items():
            age = now - data.get("last_seen", 0)
            is_complete = data.get("context", {}).get("complete", False)
            # Completed sessions expire faster
            timeout = ExerciseHTTPHandler.COMPLETED_SESSION_TIMEOUT if is_complete else ExerciseHTTPHandler.SESSION_TIMEOUT
            if age > timeout:
                stale_ids.append(sid)
        for sid in stale_ids:
            del ExerciseHTTPHandler.claude_sessions[sid]

    def _aggregate_sessions(self):
        """Aggregate context from all active sessions for display"""
        sessions = ExerciseHTTPHandler.claude_sessions
        if not sessions:
            return {}

        # Single session - return its context directly
        if len(sessions) == 1:
            return list(sessions.values())[0]["context"]

        # Multiple sessions - aggregate
        all_activity = []
        summaries = []
        active_count = 0
        complete_count = 0

        for session_id, data in sessions.items():
            ctx = data.get("context", {})
            if ctx.get("complete"):
                complete_count += 1
            else:
                active_count += 1

            if ctx.get("summary"):
                summaries.append(ctx["summary"])
            if ctx.get("recent_activity"):
                for activity in ctx["recent_activity"]:
                    # Copy to avoid mutating the original stored activity
                    all_activity.append({**activity, "session": session_id[:8]})

        # Build aggregated summary
        if active_count > 0:
            summary = f"{active_count} Claude{'s' if active_count > 1 else ''} working"
            if complete_count > 0:
                summary += f", {complete_count} done"
        elif complete_count > 0:
            summary = f"{complete_count} Claude{'s' if complete_count > 1 else ''} finished"
        else:
            summary = None

        return {
            "summary": summary,
            "session_summaries": summaries,
            "recent_activity": all_activity[:10],  # Limit to 10 most recent
            "session_count": len(sessions),
            "active_count": active_count,
            "complete_count": complete_count
        }

    def get_exercise_interface(self):
        """Load the HTML interface from the external file"""
        html_path = Path(__file__).parent / "exercise_ui.html"
        try:
            return html_path.read_text()
        except FileNotFoundError:
            return "<html><body><h1>Error: exercise_ui.html not found</h1></body></html>"

    def get_exercise_list(self):
        """Get list of all exercise definitions from exercises directory"""
        exercises_dir = Path(__file__).parent / "exercises"
        exercises = []

        if exercises_dir.exists():
            for json_file in sorted(exercises_dir.glob("*.json")):
                # Skip template and schema files
                if json_file.name.startswith("_"):
                    continue

                try:
                    content = json.loads(json_file.read_text())
                    exercises.append({
                        "id": content.get("id", json_file.stem),
                        "name": content.get("name", json_file.stem),
                        "description": content.get("description", ""),
                        "category": content.get("category", "general"),
                        "seated": content.get("seated", False),
                        "reps": content.get("reps", {"normal": 10, "quick": 5}),
                        "file": json_file.name
                    })
                except (json.JSONDecodeError, KeyError) as e:
                    # Skip invalid files
                    continue

        return exercises

    def get_exercise_file(self, filename):
        """Get content of a specific exercise file"""
        # Security: only allow .json files from exercises directory
        if not filename.endswith('.json') or '/' in filename or '\\' in filename:
            return None

        exercises_dir = Path(__file__).parent / "exercises"
        file_path = exercises_dir / filename

        # Ensure file is within exercises directory (prevent path traversal)
        try:
            file_path = file_path.resolve()
            exercises_dir = exercises_dir.resolve()
            if not str(file_path).startswith(str(exercises_dir)):
                return None
        except (ValueError, OSError):
            return None

        if file_path.exists() and file_path.is_file():
            return file_path.read_text()

        return None

    def get_asset_file(self, filename):
        """Get content of a static asset file (binary)"""
        # Security: prevent path traversal
        if '..' in filename or filename.startswith('/'):
            return None

        assets_dir = Path(__file__).parent / "assets"
        file_path = assets_dir / filename

        # Ensure file is within assets directory
        try:
            file_path = file_path.resolve()
            assets_dir = assets_dir.resolve()
            if not str(file_path).startswith(str(assets_dir)):
                return None
        except (ValueError, OSError):
            return None

        if file_path.exists() and file_path.is_file():
            return file_path.read_bytes()

        return None

    def _get_content_type(self, path):
        """Get MIME type for a file path"""
        ext = path.rsplit('.', 1)[-1].lower() if '.' in path else ''
        types = {
            'ico': 'image/x-icon',
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'webmanifest': 'application/manifest+json',
            'json': 'application/json',
        }
        return types.get(ext, 'application/octet-stream')


PORT_FILE = Path("/tmp/vibereps-port")
PORT_RANGE = range(8765, 8775)  # Try ports 8765-8774


class ExerciseTrackerHook:
    def __init__(self):
        self.port = None
        self.server = None
        self.server_thread = None
        self.shutdown_requested = False

    def _get_session_id(self, hook_data):
        """Generate a session ID from hook data (uses cwd as identifier)"""
        if hook_data and hook_data.get("cwd"):
            # Use cwd as session ID - different Claude instances have different working dirs
            import hashlib
            return hashlib.md5(hook_data["cwd"].encode()).hexdigest()[:12]
        # Fallback to default
        return "default"

    def find_available_port(self):
        """Find an available port in the range, using port binding as the lock."""
        for port in PORT_RANGE:
            try:
                # Try to bind - this is atomic and self-cleaning
                test_server = HTTPServer(('localhost', port), ExerciseHTTPHandler)
                test_server.server_close()  # Release immediately, we'll rebind
                return port
            except OSError:
                continue
        return None

    def write_port_file(self):
        """Write current port to discovery file for notify_complete.py"""
        try:
            PORT_FILE.write_text(str(self.port))
        except Exception:
            pass  # Non-critical

    def cleanup_port_file(self):
        """Remove port file on shutdown"""
        try:
            PORT_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def start_web_server(self, quick_mode=False):
        """Start a local web server to handle webcam UI"""
        # Reset completion state
        ExerciseHTTPHandler.exercise_complete = False
        ExerciseHTTPHandler.completion_data = {}
        ExerciseHTTPHandler.claude_complete = False
        ExerciseHTTPHandler.quick_mode = quick_mode
        ExerciseHTTPHandler.tracker = self  # Reference for shutdown endpoint

        # Find available port
        self.port = self.find_available_port()
        if not self.port:
            raise RuntimeError(f"No available port in range {PORT_RANGE.start}-{PORT_RANGE.stop-1}")

        # Start server
        self.server = HTTPServer(('localhost', self.port), ExerciseHTTPHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Write port to discovery file
        self.write_port_file()

        url = f"http://localhost:{self.port}"
        if quick_mode:
            url += "?quick=true"
        return url

    def wait_for_completion(self, timeout=600):
        """Wait for exercise session to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if ExerciseHTTPHandler.exercise_complete:
                return ExerciseHTTPHandler.completion_data
            time.sleep(1)

        return None

    def run_server_daemon(self, quick_mode=True):
        """Run the server in daemon mode (blocking)"""
        self.start_web_server(quick_mode=quick_mode)

        # Browser is opened by parent process, not here
        # Keep server running until completion, browser closes, or timeout

        # Shorter timeout for quick mode (2 min vs 10 min for normal)
        timeout = 120 if quick_mode else 600
        start_time = time.time()

        try:
            while time.time() - start_time < timeout:
                if ExerciseHTTPHandler.exercise_complete:
                    print("✅ Session complete!")
                    break

                # Check if shutdown was requested via /shutdown endpoint
                if self.shutdown_requested:
                    print("🛑 Shutdown requested")
                    break

                # Check if browser window was closed (Chrome process gone)
                if not is_vibereps_window_open():
                    # Give a small grace period in case browser is just slow
                    time.sleep(2)
                    if not is_vibereps_window_open():
                        print("🚪 Browser window closed")
                        break

                time.sleep(1)
        finally:
            # Always clean up
            self.cleanup_port_file()
            if self.server:
                self.server.shutdown()

    def handle_hook(self, event_type, data):
        """Main hook handler"""
        if event_type == "user_prompt_submit" or event_type == "post_tool_use":
            # For user_prompt_submit, check if the prompt is likely to result in edits
            if event_type == "user_prompt_submit":
                # Extract prompt from hook data (could be in 'prompt', 'message', or 'content')
                prompt = ""
                if data:
                    prompt = data.get("prompt") or data.get("message") or data.get("content") or ""
                    # Also check for nested structure
                    if not prompt and "input" in data:
                        prompt = data["input"].get("prompt") or data["input"].get("message") or ""

                if not prompt_likely_to_edit(prompt):
                    return {"status": "skipped", "message": "Prompt doesn't look like it will result in edits"}

            # First, check if Electron menubar app is running or can be launched
            electron_running = is_electron_app_running()

            # If Electron app is installed but not running, try to launch it
            if not electron_running and os.path.exists(ELECTRON_APP_PATH):
                if launch_electron_app():
                    electron_running = True

            if electron_running:
                # Get or create session ID (persist across hook calls, per-terminal and cwd)
                # Include cwd hash to differentiate multiple Claude instances in same parent
                cwd_hash = ""
                if data and data.get("cwd"):
                    import hashlib
                    cwd_hash = f"-{hashlib.md5(data['cwd'].encode()).hexdigest()[:8]}"
                session_id_file = Path(f"/tmp/vibereps-session-id-{os.getppid()}{cwd_hash}")
                if session_id_file.exists():
                    try:
                        session_id = session_id_file.read_text().strip()
                        # Validate session ID isn't too old (regenerate if > 1 hour)
                        if time.time() - session_id_file.stat().st_mtime > 3600:
                            session_id = generate_session_id()
                            session_id_file.write_text(session_id)
                    except (OSError, ValueError):
                        session_id = generate_session_id()
                        session_id_file.write_text(session_id)
                else:
                    session_id = generate_session_id()
                    session_id_file.write_text(session_id)

                # Build context from hook data
                context = {}
                if data:
                    tool_name = data.get("tool_name", "")
                    tool_input = data.get("tool_input", {})
                    if tool_name in ("Write", "Edit"):
                        file_path = tool_input.get("file_path", "")
                        context["summary"] = f"Editing {Path(file_path).name}" if file_path else "Editing file"
                        context["file_path"] = file_path
                    elif tool_name == "Bash":
                        command = tool_input.get("command", "")[:50]
                        context["summary"] = f"Running: {command}"

                # Register session and report activity
                register_with_electron_app(session_id, context)
                report_activity_to_electron(
                    session_id,
                    data.get("tool_name", "unknown") if data else "prompt",
                    context.get("file_path")
                )

                return {"status": "success", "message": "Activity reported to Electron app", "session_id": session_id}

            # Fall back to browser-based tracker if Electron app not running
            # Use a lock file to prevent race conditions when multiple hooks fire
            lock_file = Path("/tmp/vibereps-launch.lock")

            # Try to acquire lock (atomic check-and-create)
            try:
                # O_CREAT | O_EXCL ensures atomic creation - fails if file exists
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
            except FileExistsError:
                # Another hook is already launching, check if it's stale (> 10s old)
                try:
                    if time.time() - lock_file.stat().st_mtime < 10:
                        return {"status": "skipped", "message": "Another hook is launching exercise tracker"}
                    # Lock is stale, remove it and retry
                    lock_file.unlink(missing_ok=True)
                    fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(fd, str(os.getpid()).encode())
                    os.close(fd)
                except (FileExistsError, OSError):
                    return {"status": "skipped", "message": "Exercise tracker launch in progress"}

            # Check if server is already running (check port file first, then scan range)
            def check_server_running():
                # Try port file first
                if PORT_FILE.exists():
                    try:
                        port = int(PORT_FILE.read_text().strip())
                        urllib.request.urlopen(f"http://localhost:{port}/status", timeout=1)
                        return port
                    except (ValueError, urllib.error.URLError, OSError):
                        pass
                # Scan port range
                for port in PORT_RANGE:
                    try:
                        urllib.request.urlopen(f"http://localhost:{port}/status", timeout=0.5)
                        return port
                    except (urllib.error.URLError, OSError):
                        continue
                return None

            running_port = check_server_running()
            if running_port:
                lock_file.unlink(missing_ok=True)
                # Server already running - send updated context
                try:
                    session_id = self._get_session_id(data)
                    context = build_claude_context(data) if data else {}
                    payload = json.dumps({"session_id": session_id, "context": context}).encode()
                    req = urllib.request.Request(
                        f"http://localhost:{running_port}/update-context",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=2)
                except Exception:
                    pass  # Best effort - don't fail if update doesn't work
                return {"status": "updated", "message": "Updated context in running exercise tracker"}

            # Launch detached background process
            script_path = os.path.abspath(__file__)
            subprocess.Popen(
                [sys.executable, script_path, "--daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )

            # Give server a moment to start, then read port from file
            time.sleep(0.5)
            try:
                port = int(PORT_FILE.read_text().strip()) if PORT_FILE.exists() else PORT_RANGE.start
            except (ValueError, OSError):
                port = PORT_RANGE.start
            url = f"http://localhost:{port}?quick=true"
            exercises = get_filtered_exercises()
            if exercises:
                url += f"&exercises={exercises}"
            open_small_window(url)

            # Don't delete lock - let it stay for 10s stale window
            # This prevents duplicate windows if hooks fire in quick succession
            return {"status": "success", "message": "Exercise tracker launched in background"}

        elif event_type == "task_complete":
            # Normal mode - wait for user to complete exercises
            url = self.start_web_server(quick_mode=False)

            # Open browser
            print(f"🏋️ Exercise break triggered! Opening {url}")
            webbrowser.open(url)

            # Wait for completion
            result = self.wait_for_completion(timeout=300)  # 5 minutes max

            if result:
                print(
                    f"✅ Exercise complete! {result.get('reps', 0)} reps of {result.get('exercise', 'unknown')}")
            else:
                print("⏱️ Session timeout or window closed")

            # Shutdown server
            if self.server:
                self.server.shutdown()

            return {"status": "success", "message": "Exercise tracker completed", "data": result}

        return {"status": "skipped", "message": f"Event type {event_type} not handled"}


CONTEXT_FILE = Path("/tmp/vibereps-context.json")


def read_hook_payload_from_stdin() -> dict:
    """Read Claude Code hook payload from stdin (non-blocking)."""
    import select

    # Check if there's data on stdin (non-blocking)
    if select.select([sys.stdin], [], [], 0.1)[0]:
        try:
            return json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def main():
    # Check if running as daemon
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Load initial session from temp file (written by parent process)
        if CONTEXT_FILE.exists():
            try:
                data = json.loads(CONTEXT_FILE.read_text())
                session_id = data.get("session_id", "default")
                context = data.get("context", data)  # Support old format too
                ExerciseHTTPHandler.claude_sessions[session_id] = {
                    "context": context,
                    "last_seen": time.time()
                }
            except (json.JSONDecodeError, OSError):
                pass

        # Run server in daemon mode
        tracker = ExerciseTrackerHook()
        tracker.run_server_daemon(quick_mode=True)
        return 0

    # Parse Claude Code hook event
    if len(sys.argv) > 1:
        event_type = sys.argv[1]
        # Command line arg is usually '{}', real data comes from stdin
        _ = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    else:
        # Test mode
        event_type = "post_tool_use"

    # Read actual hook payload from stdin (Claude Code passes it there)
    hook_data = read_hook_payload_from_stdin()

    # Initialize tracker first (needed for session ID generation)
    tracker = ExerciseTrackerHook()

    # Build context from hook payload + transcript
    if hook_data:
        context = build_claude_context(hook_data)
        session_id = tracker._get_session_id(hook_data)
        # Write context with session_id to temp file for daemon to read
        try:
            CONTEXT_FILE.write_text(json.dumps({"session_id": session_id, "context": context}))
        except OSError:
            pass

    # Run tracker
    result = tracker.handle_hook(event_type, hook_data)

    print(json.dumps(result))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
