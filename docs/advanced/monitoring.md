# Usage Tracking

View your Claude Code usage alongside exercise data with `vibereps-usage`.

## Quick Start

```bash
# View combined usage and exercise data
./vibereps-usage.py

# Or run from anywhere
python ~/.vibereps/vibereps-usage.py
```

## Output

```
==================================================================================================================================
Date         Models                              Input       Output          Total       Cost Exercises
==================================================================================================================================
2026-01-05   haiku-4-5, opus-4-5                21,091        2,937      3,033,566     $25.21 15 squats, 10 JJ
2026-01-06   haiku-4-5, opus-4-5               113,396       10,142      5,548,007     $53.68 20 squats, 15 calf raises
2026-01-07   haiku-4-5, opus-4-5                66,590        9,252      6,984,936     $66.70 25 squats
==================================================================================================================================
Total                                          201,077       22,331     15,566,509    $145.59 60 squats, 25 calf raises, 10 JJ
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
