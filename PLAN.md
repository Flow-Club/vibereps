# Implementation Plan: Privacy-Preserving Remote Stat Sync

## Overview

Add opt-in remote stat syncing with a privacy-preserving username system. Users can:
1. Log exercises locally only (default, no account needed)
2. Opt-in to remote sync with a display name they choose
3. View global leaderboard and stats via MCP

## Current State

- **Local logging**: `~/.vibereps/exercises.jsonl` (works without account)
- **Remote logging**: Requires env vars `VIBEREPS_API_URL` + `VIBEREPS_API_KEY`
- **User creation**: `POST /api/users` with username, returns API key
- **No config file**: Settings via env vars only

## Design Decisions

### Username/Identity

**Approach: User-chosen display name with anonymous fallback**

- User picks a display name when opting in (e.g., "flowclub", "ninja_coder")
- If they skip/decline, auto-generate `anon_XXXX` (4 random chars)
- Display names are unique but can be changed later
- No email, no machine identifiers, no PII collected

**Privacy guarantees:**
- Only display name shown on leaderboard
- No correlation to real identity unless user chooses
- Can use anonymous name and still participate

### Configuration Storage

```json
// ~/.vibereps/config.json
{
  "version": 1,
  "local_logging": true,
  "remote_sync": {
    "enabled": false,
    "api_url": "https://vibereps.flowclub.co",
    "api_key": null,
    "display_name": null
  }
}
```

**Precedence**: Environment variables override config file (for CI/testing)

## Implementation Tasks

### Phase 1: Config File Support ✅ DONE

#### 1.1 Create config module (`vibereps_config.py`) ✅

```python
# New file: vibereps_config.py
"""
Configuration management for VibeReps.
Handles reading/writing ~/.vibereps/config.json
"""

CONFIG_PATH = Path.home() / ".vibereps" / "config.json"
DEFAULT_API_URL = "https://vibereps.flowclub.co"

def load_config() -> dict:
    """Load config, merging with defaults."""

def save_config(config: dict) -> None:
    """Save config to file."""

def get_remote_settings() -> tuple[str, str] | None:
    """Get (api_url, api_key) if remote sync enabled, else None.
    Env vars override config file."""
```

#### 1.2 Update `exercise_tracker.py` ✅

- Import and use `vibereps_config.load_config()`
- Fallback chain: env var → config file → disabled
- Keep backward compatibility with existing env var users

### Phase 2: Interactive Setup ✅ DONE

#### 2.1 Create setup script (`vibereps_setup.py`) ✅

Interactive CLI that:
1. Explains what remote sync does
2. Asks if user wants to enable it (default: no)
3. If yes, prompts for display name
4. Creates account on server, saves credentials to config
5. Shows confirmation with display name

```
$ ./vibereps_setup.py

VibeReps Remote Sync Setup
==========================

Remote sync lets you:
- See your stats on the global leaderboard
- Track your streak across devices
- Compare with other Claude Code users

Your exercise data (reps, timestamps) will be sent to our server.
Video/images never leave your browser.

Enable remote sync? [y/N]: y

Choose a display name for the leaderboard.
This is public - don't use your real name if you want privacy.
Leave blank for anonymous (anon_XXXX).

Display name: flowclub

Creating account... done!

Your display name: flowclub
Your streak: 0 days
Leaderboard rank: #47

Config saved to ~/.vibereps/config.json
```

#### 2.2 Add `/setup-vibereps` skill enhancement

Update the existing skill to include remote sync option:
- Add "Enable remote stats" as a choice
- Run `vibereps_setup.py` interactively

### Phase 3: Server Changes ✅ DONE

#### 3.1 Anonymous username support ✅

- Allow `username` to be null/empty in `POST /api/users`
- Auto-generate `anon_XXXX` if not provided
- Validate uniqueness of display names

#### 3.2 Username change endpoint ✅

```
PUT /api/users/me/display-name
{"display_name": "new_name"}
```

- Validate uniqueness
- Allow changing from anonymous to chosen name

#### 3.3 Leaderboard privacy ✅

- Only show display_name (already the case)
- Added `GET /api/users/me` endpoint for profile

### Phase 4: Install Script Integration ✅ DONE

#### 4.1 Update `install.sh` ✅

Added `setup_remote_sync()` function that:
- Prompts user to enable remote sync
- Asks for display name (blank = anonymous)
- Calls `vibereps_setup.py --non-interactive`
- Shows remote sync status in summary

Environment variable `VIBEREPS_REMOTE_SYNC=skip` skips the prompt.

### Phase 5: MCP Server Updates ✅ DONE

#### 5.1 Add identity tools ✅

New MCP tools for Claude to help users:
- `get_my_profile` - Show user's display name, rank, stats
- `update_display_name` - Change display name (with confirmation)

## File Changes Summary

| File | Change | Status |
|------|--------|--------|
| `vibereps_config.py` | NEW - Config management | ✅ Done |
| `vibereps_setup.py` | NEW - Interactive setup CLI | ✅ Done |
| `exercise_tracker.py` | Use config module, keep env var compat | ✅ Done |
| `server/main.py` | Anonymous username, display name change, new MCP tools | ✅ Done |
| `install.sh` | Optional remote sync prompt | ✅ Done |
| `.claude/skills/setup-vibereps/SKILL.md` | Add remote sync option | ✅ Done |

## Security Considerations

1. **API key storage**: Config file should have 0600 permissions
2. **Anonymous names**: Use `secrets.token_hex(2)` for 4 random hex chars
3. **Rate limiting**: Prevent username enumeration via rate limits
4. **Display name validation**: Alphanumeric + underscore, 3-20 chars

## Testing Plan

1. Fresh install - should work without remote sync
2. Setup flow - create account, verify on server
3. Existing env var users - should still work
4. Anonymous user - verify `anon_XXXX` generated
5. Leaderboard - verify only display names shown

## Migration

Existing users with env vars continue working. Config file is additive.

## Default Server URL

For the public hosted version:
- `https://vibereps.flowclub.co` (to be deployed)
- Fallback: Users can self-host and specify custom URL
