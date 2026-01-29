# Usage Tracking

View your Claude Code usage alongside exercise data with `vibereps-usage`.

<p align="center">
  <img src="/vibereps-usage.gif" alt="vibereps-usage demo" style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
</p>

## Powered by ccusage

This feature is built on [**ccusage**](https://github.com/ryoppippi/ccusage) by [@ryoppippi](https://github.com/ryoppippi) - an excellent CLI tool for tracking Claude Code token usage and costs. We were inspired by ccusage's clean table format and built `vibereps-usage.py` to add exercise data alongside your coding stats.

If you just want Claude Code usage tracking without exercise data, ccusage is all you need:

```bash
npm install -g ccusage
ccusage daily
```

## Quick Start

```bash
# View combined usage and exercise data
./vibereps-usage.py

# Or run from anywhere
python ~/.vibereps/vibereps-usage.py
```

## How It Works

1. Exercise data is logged to `~/.vibereps/exercises.jsonl` on each completion
2. `vibereps-usage.py` reads this file and combines it with `ccusage` output
3. Both data sources are grouped by date for a unified view

## Options

```bash
# Pass arguments through to ccusage
./vibereps-usage.py --since 2026-01-01

# Show only exercise data (no ccusage)
./vibereps-usage.py --exercises-only
```

## Data Files

| File | Description |
|------|-------------|
| `~/.vibereps/exercises.jsonl` | Local exercise log (one JSON object per line) |
| `~/.claude/statsig/usage.jsonl` | Claude Code usage (read by ccusage) |

## Exercise Log Format

Each exercise completion is logged as:

```json
{"timestamp": "2026-01-13T10:30:00", "exercise": "squats", "reps": 5, "duration": 45, "mode": "quick"}
```

## Requirements

- [ccusage](https://github.com/ryoppippi/ccusage) - `npm install -g ccusage`
- Python 3 (standard library only)
