# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by:

1. **Do NOT open a public issue**
2. Email the maintainers or open a private security advisory on GitHub

We will respond within 48 hours and work with you to understand and resolve the issue.

## Security Considerations

### Local Exercise Tracker

- All video processing happens client-side in the browser
- No video data is transmitted or stored
- The local server only listens on `localhost:8765`
- Exercise data (reps, timestamps) is stored locally in `~/.vibereps/exercises.jsonl`

### Remote Server (Optional)

- API keys are generated using `secrets.token_hex(32)`
- Passwords and keys should be stored in environment variables, not in code
- The server uses SQLAlchemy ORM to prevent SQL injection

### Browser Security

- MediaPipe is loaded from Google's CDN over HTTPS
- No external requests are made except for MediaPipe assets
- Camera access requires explicit user permission
