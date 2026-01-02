#!/usr/bin/env python3
"""
exercise_tracker.py - Claude Code hook for exercise tracking
Place this in your hooks directory and make it executable
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


# Configuration - set these environment variables or edit directly
VIBEREPS_API_URL = os.getenv("VIBEREPS_API_URL", "")  # e.g., "https://vibereps.example.com"
VIBEREPS_API_KEY = os.getenv("VIBEREPS_API_KEY", "")  # Your API key
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")  # Prometheus Pushgateway
VIBEREPS_EXERCISES = os.getenv("VIBEREPS_EXERCISES", "")  # Comma-separated: "squats,pushups,jumping_jacks"


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


def log_to_prometheus(exercise: str, reps: int, duration: int = 0, mode: str = "normal") -> bool:
    """Push exercise metrics to Prometheus Pushgateway."""
    if not PUSHGATEWAY_URL:
        return False

    # Sanitize labels
    exercise = "".join(c if c.isalnum() or c in "-_" else "_" for c in exercise)
    mode = "".join(c if c.isalnum() or c in "-_" else "_" for c in mode)

    from datetime import datetime
    timestamp = datetime.now().timestamp()

    metrics = f"""# HELP exercise_reps_total Total exercise reps completed
# TYPE exercise_reps_total counter
exercise_reps_total{{exercise="{exercise}",mode="{mode}"}} {reps}
# HELP exercise_sessions_total Total exercise sessions completed
# TYPE exercise_sessions_total counter
exercise_sessions_total{{exercise="{exercise}",mode="{mode}"}} 1
# HELP exercise_duration_seconds_total Total exercise duration in seconds
# TYPE exercise_duration_seconds_total counter
exercise_duration_seconds_total{{exercise="{exercise}",mode="{mode}"}} {duration}
# HELP exercise_last_session_timestamp Timestamp of last exercise session
# TYPE exercise_last_session_timestamp gauge
exercise_last_session_timestamp{{exercise="{exercise}",mode="{mode}"}} {timestamp}
# HELP exercise_last_session_reps Reps in most recent session
# TYPE exercise_last_session_reps gauge
exercise_last_session_reps{{exercise="{exercise}",mode="{mode}"}} {reps}
"""

    job_name = "exercise_tracker"
    url = f"{PUSHGATEWAY_URL}/metrics/job/{job_name}/exercise/{exercise}/mode/{mode}"

    try:
        req = urllib.request.Request(
            url,
            data=metrics.encode("utf-8"),
            method="POST"
        )
        req.add_header("Content-Type", "text/plain")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except urllib.error.URLError:
        # Pushgateway not available, silently ignore
        return False
    except Exception:
        return False


class ExerciseHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler to serve the exercise UI and handle completion"""

    exercise_complete = False
    completion_data = {}
    claude_complete = False
    quick_mode = False

    def do_GET(self):
        """Serve the exercise tracker HTML"""
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

                remote_logged = log_to_remote(exercise, reps, duration)
                prometheus_logged = log_to_prometheus(exercise, reps, duration, mode)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "remote_logged": remote_logged,
                    "prometheus_logged": prometheus_logged
                }).encode())
            except Exception as e:
                self.send_error(500, str(e))
        elif self.path == '/notify':
            # Notification from Claude that it's done
            try:
                ExerciseHTTPHandler.claude_complete = True

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "notified"}).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """Suppress server logs"""
        pass

    def get_exercise_interface(self):
        """Load the HTML interface from the external file"""
        html_path = Path(__file__).parent / "exercise_ui.html"
        try:
            return html_path.read_text()
        except FileNotFoundError:
            return "<html><body><h1>Error: exercise_ui.html not found</h1></body></html>"


class ExerciseTrackerHook:
    def __init__(self):
        self.port = 8765
        self.server = None
        self.server_thread = None

    def start_web_server(self, quick_mode=False):
        """Start a local web server to handle webcam UI"""
        # Reset completion state
        ExerciseHTTPHandler.exercise_complete = False
        ExerciseHTTPHandler.completion_data = {}
        ExerciseHTTPHandler.claude_complete = False
        ExerciseHTTPHandler.quick_mode = quick_mode

        # Start server
        self.server = HTTPServer(('localhost', self.port), ExerciseHTTPHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

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
        url = self.start_web_server(quick_mode=quick_mode)

        # Browser is opened by parent process, not here
        # Keep server running until user closes browser or timeout

        # Wait for either completion or timeout (10 minutes max)
        start_time = time.time()
        while time.time() - start_time < 600:
            if ExerciseHTTPHandler.exercise_complete:
                print("✅ Session complete!")
                break
            time.sleep(1)

        # Shutdown server
        if self.server:
            self.server.shutdown()

    def handle_hook(self, event_type, data):
        """Main hook handler"""
        if event_type == "user_prompt_submit" or event_type == "post_tool_use":
            # Launch as detached background process
            script_path = os.path.abspath(__file__)

            # Check if server is already running
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:8765/status", timeout=1)
                # Server already running, skip
                return {"status": "skipped", "message": "Exercise tracker already running"}
            except BaseException:
                # Server not running, launch it
                pass

            # Launch detached background process
            subprocess.Popen(
                [sys.executable, script_path, "--daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )

            # Give server a moment to start, then open browser from this process
            time.sleep(0.5)
            url = f"http://localhost:{self.port}?quick=true"
            if VIBEREPS_EXERCISES:
                url += f"&exercises={VIBEREPS_EXERCISES}"
            webbrowser.open(url)

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


def main():
    # Check if running as daemon
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Run server in daemon mode
        tracker = ExerciseTrackerHook()
        tracker.run_server_daemon(quick_mode=True)
        return 0

    # Parse Claude Code hook event
    if len(sys.argv) > 1:
        event_type = sys.argv[1]
        data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    else:
        # Test mode
        event_type = "post_tool_use"
        data = {}

    # Initialize and run tracker
    tracker = ExerciseTrackerHook()
    result = tracker.handle_hook(event_type, data)

    print(json.dumps(result))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
