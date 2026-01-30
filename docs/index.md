---
layout: home

hero:
  name: VibeReps
  text: Tend to your quads while you tend to your Claudes.
  tagline: Do exercises and think a little yourself while you wait for Claude.
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/Flow-Club/vibereps

features:
  - icon: 🏋️
    title: Real-time Pose Detection
    details: MediaPipe AI tracks your movements in-browser. No video leaves your computer.
  - icon: ⚡
    title: Quick Exercise Breaks
    details: Keep moving while Claude processes your request. Exercises cycle until Claude is ready.
  - icon: 🔔
    title: Smart Notifications
    details: Desktop alerts when Claude is ready. Exercise while you wait, come back when it's done.
  - icon: 🎯
    title: Multiple Exercises
    details: Squats, push-ups, jumping jacks, calf raises, and more. Variety keeps it interesting.
---

## How It Works

```
You: "Hey Claude, refactor this code"
    ↓
🏋️ Exercise tracker launches (5 squats)
    ↓
You exercise  ←→  Claude processes your request
    ↓
Exercise complete → "⏳ Claude is working..."
    ↓
Claude: "Here's your refactored code"
    ↓
🔔 Desktop notification: "Claude is ready!"
    ↓
You return to check the response
```

## See It In Action

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; margin: 1.5rem 0;">
  <iframe
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 8px;"
    src="https://www.youtube.com/embed/S0owNK_xSCA"
    title="VibeReps Demo"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen>
  </iframe>
</div>

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash
```

This installs the **menubar app** (recommended). For browser-only mode, add `--webapp`:

```bash
curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash -s -- --webapp
```

Then restart Claude Code and run **`/vibereps`** to choose your exercises.
