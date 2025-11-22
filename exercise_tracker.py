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


class ExerciseHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler to serve the exercise UI and handle completion"""

    exercise_complete = False
    completion_data = {}
    claude_complete = False
    quick_mode = False

    def do_GET(self):
        """Serve the exercise tracker HTML"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html_content = self.get_exercise_interface()
            self.wfile.write(html_content.encode())
        elif self.path == '/status':
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

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
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
        """Create the HTML interface with webcam access and pose detection"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Claude Code Exercise Break</title>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/pose.js" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils@0.3.1640029074/camera_utils.js" crossorigin="anonymous"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            max-width: 800px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        h1 {
            margin: 0 0 20px 0;
            font-size: 2em;
            text-align: center;
        }
        .exercise-selector {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
            font-weight: 500;
        }
        button:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        button.active {
            background: rgba(255,255,255,0.4);
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        #videoContainer {
            position: relative;
            margin: 20px 0;
            border-radius: 10px;
            overflow: hidden;
            display: none;
        }
        #videoContainer.active {
            display: block;
        }
        video {
            width: 100%;
            max-width: 640px;
            height: auto;
            border-radius: 10px;
            display: block;
        }
        canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        .counter {
            font-size: 3em;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
        }
        .status {
            text-align: center;
            font-size: 1.2em;
            margin: 10px 0;
        }
        .finish-btn {
            background: rgba(76, 175, 80, 0.3);
            margin-top: 20px;
        }
        .finish-btn:hover {
            background: rgba(76, 175, 80, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏋️ Vibe Reps</h1>
        <p style="text-align: center;">Time to move! Select an exercise and get your reps in:</p>

        <div class="exercise-selector" id="exerciseSelector">
            <button onclick="startExercise('squats')" id="squatsBtn">Squats (<span class="rep-count">10</span>)</button>
            <button onclick="startExercise('pushups')" id="pushupsBtn">Push-ups (<span class="rep-count">10</span>)</button>
            <button onclick="startExercise('jumping_jacks')" id="jjBtn">Jumping Jacks (<span class="rep-count">20</span>)</button>
        </div>

        <div id="videoContainer">
            <video id="video" autoplay playsinline muted></video>
            <canvas id="canvas" width="640" height="480"></canvas>
        </div>

        <div class="counter" id="counter">0</div>
        <div class="status" id="status">Select an exercise to begin!</div>

        <button class="finish-btn" onclick="finishSession()">Finish Session</button>
    </div>

    <script>
        let currentExercise = null;
        let repCount = 0;
        let targetReps = {squats: 10, pushups: 10, jumping_jacks: 20};
        let quickModeReps = {squats: 5, pushups: 5, jumping_jacks: 10};
        let exerciseState = null;
        let pose = null;
        let camera = null;
        let startTime = null;
        let statusPollInterval = null;
        let isQuickMode = new URLSearchParams(window.location.search).get('quick') === 'true';

        // Set up quick mode if enabled
        if (isQuickMode) {
            targetReps = quickModeReps;
            document.querySelector('#squatsBtn .rep-count').textContent = quickModeReps.squats;
            document.querySelector('#pushupsBtn .rep-count').textContent = quickModeReps.pushups;
            document.querySelector('#jjBtn .rep-count').textContent = quickModeReps.jumping_jacks;
            document.querySelector('h1').innerHTML = '⚡ Quick Exercise Break!';
            document.querySelector('p').textContent = 'Quick session while Claude works!';
        }

        // Initialize MediaPipe Pose
        async function initPose() {
            if (typeof Pose === 'undefined') {
                document.getElementById('status').textContent = 'Error: MediaPipe libraries not loaded';
                return false;
            }

            pose = new Pose({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/${file}`;
                }
            });

            pose.setOptions({
                modelComplexity: 1,
                smoothLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            pose.onResults(onPoseResults);
            return true;
        }

        async function startExercise(exercise) {
            currentExercise = exercise;
            repCount = 0;
            exerciseState = 'ready';
            startTime = Date.now();

            // Update UI
            document.querySelectorAll('.exercise-selector button').forEach(btn => {
                btn.classList.remove('active');
                btn.disabled = true;
            });
            document.getElementById(exercise + 'Btn').classList.add('active');
            document.getElementById('counter').textContent = '0';
            document.getElementById('status').textContent = 'Requesting camera access...';

            try {
                // Start webcam
                const video = document.getElementById('video');
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: 640,
                        height: 480
                    }
                });
                video.srcObject = stream;

                document.getElementById('videoContainer').classList.add('active');
                document.getElementById('status').textContent = 'Get in position...';

                // Initialize pose detection if not already done
                if (!pose) {
                    const success = await initPose();
                    if (!success) return;
                }

                // Start camera feed to pose detection
                if (typeof Camera !== 'undefined') {
                    camera = new Camera(video, {
                        onFrame: async () => {
                            await pose.send({image: video});
                        },
                        width: 640,
                        height: 480
                    });
                    await camera.start();
                } else {
                    document.getElementById('status').textContent = 'Error: Camera utils not loaded';
                }

            } catch (error) {
                document.getElementById('status').textContent = 'Error accessing camera: ' + error.message;
                console.error('Camera error:', error);

                // Re-enable buttons
                document.querySelectorAll('.exercise-selector button').forEach(btn => {
                    btn.disabled = false;
                });
            }
        }

        function onPoseResults(results) {
            // Draw pose landmarks
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (results.poseLandmarks) {
                // Simple exercise detection logic
                detectExercise(results.poseLandmarks);

                // Draw skeleton
                ctx.strokeStyle = '#00FF00';
                ctx.lineWidth = 2;
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#00FF00';
                drawConnectors(ctx, results.poseLandmarks);

                // Draw joints
                ctx.fillStyle = '#00FF00';
                results.poseLandmarks.forEach(landmark => {
                    ctx.beginPath();
                    ctx.arc(landmark.x * 640, landmark.y * 480, 5, 0, 2 * Math.PI);
                    ctx.fill();
                });
            }
        }

        function detectExercise(landmarks) {
            if (!currentExercise) return;

            if (currentExercise === 'squats') {
                detectSquat(landmarks);
            } else if (currentExercise === 'pushups') {
                detectPushup(landmarks);
            } else if (currentExercise === 'jumping_jacks') {
                detectJumpingJack(landmarks);
            }
        }

        function detectSquat(landmarks) {
            // Check hip and knee angles for squat detection
            const hip = landmarks[23];
            const knee = landmarks[25];
            const ankle = landmarks[27];

            if (hip && knee && ankle) {
                const angle = calculateAngle(hip, knee, ankle);

                if (angle < 100 && exerciseState !== 'down') {
                    exerciseState = 'down';
                    document.getElementById('status').textContent = 'Going down... ⬇️';
                } else if (angle > 160 && exerciseState === 'down') {
                    exerciseState = 'up';
                    repCount++;
                    updateCounter();
                }
            }
        }

        function detectPushup(landmarks) {
            // Detect push-up based on elbow angle
            const shoulder = landmarks[11];
            const elbow = landmarks[13];
            const wrist = landmarks[15];

            if (shoulder && elbow && wrist) {
                const angle = calculateAngle(shoulder, elbow, wrist);

                if (angle < 90 && exerciseState !== 'down') {
                    exerciseState = 'down';
                    document.getElementById('status').textContent = 'Going down... ⬇️';
                } else if (angle > 150 && exerciseState === 'down') {
                    exerciseState = 'up';
                    repCount++;
                    updateCounter();
                }
            }
        }

        function detectJumpingJack(landmarks) {
            // Detect based on arm position
            const leftWrist = landmarks[15];
            const rightWrist = landmarks[16];
            const leftShoulder = landmarks[11];
            const rightShoulder = landmarks[12];

            if (leftWrist && rightWrist && leftShoulder && rightShoulder) {
                const armsUp = leftWrist.y < leftShoulder.y && rightWrist.y < rightShoulder.y;

                if (armsUp && exerciseState !== 'up') {
                    exerciseState = 'up';
                    repCount++;
                    updateCounter();
                } else if (!armsUp && exerciseState === 'up') {
                    exerciseState = 'down';
                }
            }
        }

        function calculateAngle(a, b, c) {
            const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
            let angle = Math.abs(radians * 180.0 / Math.PI);
            if (angle > 180.0) angle = 360 - angle;
            return angle;
        }

        function drawConnectors(ctx, landmarks) {
            // Simplified connector drawing
            const connections = [
                [11, 13], [13, 15], // Left arm
                [12, 14], [14, 16], // Right arm
                [11, 23], [12, 24], // Torso
                [23, 25], [25, 27], // Left leg
                [24, 26], [26, 28], // Right leg
                [11, 12], [23, 24], // Shoulders and hips
            ];

            connections.forEach(([start, end]) => {
                if (landmarks[start] && landmarks[end]) {
                    ctx.beginPath();
                    ctx.moveTo(landmarks[start].x * 640, landmarks[start].y * 480);
                    ctx.lineTo(landmarks[end].x * 640, landmarks[end].y * 480);
                    ctx.stroke();
                }
            });
        }

        function updateCounter() {
            document.getElementById('counter').textContent = repCount;

            if (repCount >= targetReps[currentExercise]) {
                document.getElementById('status').textContent = '🎉 Great job! Exercise complete!';

                // Stop camera
                if (camera) {
                    camera.stop();
                }
                const video = document.getElementById('video');
                if (video.srcObject) {
                    video.srcObject.getTracks().forEach(track => track.stop());
                }
                document.getElementById('videoContainer').classList.remove('active');

                if (isQuickMode) {
                    // In quick mode, wait and then show "Claude is working" status
                    setTimeout(() => {
                        document.getElementById('status').textContent = '⏳ Claude is working on your request...';
                        document.getElementById('exerciseSelector').style.display = 'none';
                        document.querySelector('.finish-btn').textContent = 'Waiting for Claude...';
                        document.querySelector('.finish-btn').disabled = true;

                        // Start polling for Claude completion
                        startStatusPolling();
                    }, 2000);
                } else {
                    // Normal mode - re-enable buttons for next exercise
                    setTimeout(() => {
                        document.querySelectorAll('.exercise-selector button').forEach(btn => {
                            btn.disabled = false;
                            btn.classList.remove('active');
                        });

                        exerciseState = null;
                        document.getElementById('status').textContent = 'Great work! Pick another exercise or finish session.';
                    }, 2000);
                }
            } else {
                const remaining = targetReps[currentExercise] - repCount;
                document.getElementById('status').textContent = `Keep going! ${remaining} more! 💪`;
            }
        }

        function startStatusPolling() {
            if (statusPollInterval) return; // Already polling

            statusPollInterval = setInterval(async () => {
                try {
                    const response = await fetch('/status');
                    const status = await response.json();

                    if (status.claude_complete) {
                        clearInterval(statusPollInterval);
                        showClaudeCompleteNotification();
                    }
                } catch (error) {
                    console.error('Status poll error:', error);
                }
            }, 1000); // Poll every second
        }

        function showClaudeCompleteNotification() {
            document.getElementById('status').textContent = '✅ Claude is ready! Check your response.';
            document.querySelector('.finish-btn').textContent = 'Return to Claude Code';
            document.querySelector('.finish-btn').disabled = false;
            document.querySelector('.finish-btn').onclick = () => window.close();

            // Desktop notification
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Claude Code Ready!', {
                    body: 'Your request is complete. Check Claude Code!',
                    icon: '🤖'
                });
            } else if ('Notification' in window && Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification('Claude Code Ready!', {
                            body: 'Your request is complete. Check Claude Code!',
                            icon: '🤖'
                        });
                    }
                });
            }

            // Play sound alert (optional)
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiDYIGGS46ummTgwNUKzn8LdmHAU9kdz0y3krBSp+zPLaizsKE1+36eyrWRIJSKHh87ljHgU2fcrx24k4ChdbsuXqpVELDFCt5++8aB8GOpHb9Ml5KwUlfcry2I89ChNguuvrs1kSCUuf4PPAaCAGN4HL8tyJNwoZZbjo6qZPDA5RruXwvGgfBTyS2/fLeSsGKX/L8tqLOwoSX7Tl6qxZEwlHoOHz'
                );
                audio.play().catch(() => {}); // Ignore errors
            } catch (e) {}
        }

        function finishSession() {
            // Calculate duration
            const duration = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;

            // Send completion message back to hook
            fetch('/complete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    completed: true,
                    reps: repCount,
                    exercise: currentExercise,
                    duration: duration
                })
            }).then(() => {
                document.getElementById('status').textContent = '✅ Session logged! You can close this window.';
                setTimeout(() => {
                    window.close();
                }, 2000);
            }).catch(err => {
                console.error('Error logging session:', err);
                document.getElementById('status').textContent = 'Session complete! You can close this window.';
            });
        }
    </script>
</body>
</html>
        '''


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

        # Open browser
        print(f"⚡ Quick exercise session! Opening {url}")
        webbrowser.open(url)

        # Keep server running until user closes browser or timeout
        print("🏋️ Server running... Close browser window to exit.")

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
            except:
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
