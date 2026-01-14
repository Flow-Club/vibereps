# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--dangerously-skip-leg-day` feature via `VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY=1`
- `vibereps-usage.py` for combined Claude Code + exercise stats
- `config.json` with array of taglines
- 11 exercise types with JSON-based configuration
- Chin tucks exercise for posture correction

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
