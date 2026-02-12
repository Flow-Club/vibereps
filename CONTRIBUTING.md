# Contributing to VibeReps

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Flow-Club/vibereps.git
   cd vibereps
   ```

2. Install for local development:
   ```bash
   ./install.sh
   ```

3. Test the exercise tracker:
   ```bash
   VIBEREPS_EXERCISES=squats ./vibereps.py post_tool_use '{}'
   ```

## Project Structure

```
vibereps/
├── vibereps.py            # Main hook script (exercise tracking + notifications)
├── exercise_ui.html       # Browser UI with pose detection
├── notify_complete.py     # Deprecated wrapper (forwards to vibereps.py)
├── exercises/             # Exercise JSON configs
├── server/                # Optional remote server
├── docs/                  # VitePress documentation site
└── config.json            # Project metadata
```

## Adding a New Exercise

1. Create a JSON config in `exercises/`:
   ```json
   {
     "id": "my_exercise",
     "name": "My Exercise",
     "description": "What it does",
     "category": "strength",
     "reps": { "normal": 10, "quick": 5 },
     "detection": { ... },
     "instructions": { ... }
   }
   ```

2. See `exercises/_template.json` for the full schema.

3. Test with:
   ```bash
   VIBEREPS_EXERCISES=my_exercise ./vibereps.py post_tool_use '{}'
   ```

## Code Style

- Python: Follow PEP 8
- JavaScript: No build step, keep it simple
- Keep dependencies minimal (Python stdlib where possible)

## Pull Requests

1. Fork the repo and create a branch
2. Make your changes
3. Test locally with the exercise tracker
4. Submit a PR with a clear description

## Documentation

The docs site uses VitePress:

```bash
cd docs
npm install
npm run dev
```

## Questions?

Open an issue or start a discussion on GitHub.
