# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-01-29

### Added
- Window position memory - Electron app remembers where you put it
- `vibereps-usage.py` documentation with demo GIF in README and docs
- Architecture diagrams updated to show local JSONL logging flow

### Fixed
- Camera light stays off until window is actually shown (deferred enumeration)
- Camera stops when Electron window is hidden (no more always-on light)
- Window bounds validation requires 100px visible (prevents off-screen windows)
- Fixed 'Object has been destroyed' errors in Electron
- Fixed exercise logging in Electron - use IPC instead of HTTP
- Fixed IndentationError in exercise_tracker.py for UserPromptSubmit hook
- Fixed MediaPipe loading race conditions

### Changed
- Responsive UI scaling with distance-based font sizing
- Updated hooks documentation to mark prompt trigger mode as experimental
- Added attribution to ccusage as inspiration for usage tracking

## [0.2.0] - 2026-01-28

### Added
- Electron menubar app for macOS with multi-instance session tracking
- Async hook execution (`"async": true`) for non-blocking operation
- `VIBEREPS_DISABLED` environment variable to disable tracking
- `VIBEREPS_UI_MODE` environment variable (electron/webapp)
- `VIBEREPS_TRIGGER_MODE` environment variable (edit-only/prompt)
- Smart prompt detection for `user_prompt_submit` mode
- Session manager for tracking multiple Claude instances
- Bundled MediaPipe for offline use in Electron app
- DMG distribution support

### Fixed
- XSS vulnerability in exercise_ui.html (escaped HTML in dynamic content)

### Changed
- Two-tier port architecture: Electron uses 8800, webapp uses 8765-8774
- Notification hook matcher changed to `idle_prompt|permission_prompt`

## [0.1.1] - 2026-01-15

### Added
- `--dangerously-skip-leg-day` feature via `VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY=1`
- `vibereps-usage.py` for combined Claude Code + exercise stats
- `config.json` with array of taglines
- 11 exercise types with JSON-based configuration

### Changed
- Exercise configs moved from hardcoded JS to `exercises/*.json`
- Simplified monitoring: removed Prometheus/Grafana, now uses local JSONL + ccusage

### Fixed
- Daemon now detects when browser window closes
- Shorter timeout for quick mode (2 min vs 10 min)

## [0.1.0] - 2024-01-13

### Added
- Initial release
- PostToolUse hook integration for Claude Code
- Real-time pose detection with MediaPipe
- Quick mode (5 reps) and normal mode (10+ reps)
- Desktop notifications when Claude is ready
- Local exercise logging to JSONL
- Optional remote server for stats and leaderboards
- One-line installer script
