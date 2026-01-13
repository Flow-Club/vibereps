# Usage Tracking

**Note:** The Docker Compose stack (Prometheus/Grafana) in this directory is deprecated. Use `vibereps-usage.py` instead for a simpler approach.

## Recommended: vibereps-usage

```bash
# View combined Claude Code usage + exercise data
./vibereps-usage.py

# Or from anywhere
python ~/.vibereps/vibereps-usage.py
```

See [docs/advanced/monitoring.md](../docs/advanced/monitoring.md) for details.

## Legacy Docker Stack

The Docker Compose files remain for reference but are no longer maintained. If you previously used this:

```bash
# Stop and remove
docker-compose down -v
```
