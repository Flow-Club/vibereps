#!/bin/bash
# VibeReps Electron App Installer
# Builds and installs the menubar app to /Applications
# Optionally configures Claude Code hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

cd "$SCRIPT_DIR"

echo "=== VibeReps Menubar App Installer ==="
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    echo "Install it from https://nodejs.org/ or via: brew install node"
    exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed."
    exit 1
fi

# Check for jq (for JSON manipulation)
HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

echo "1. Installing dependencies..."
npm install --silent

echo "2. Building app..."
npm run build --silent 2>/dev/null || npm run build

# Determine architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    APP_PATH="dist/mac-arm64/VibeReps.app"
else
    APP_PATH="dist/mac/VibeReps.app"
fi

if [ ! -d "$APP_PATH" ]; then
    echo "Error: Build failed - $APP_PATH not found"
    exit 1
fi

echo "3. Installing to /Applications..."

# Remove old version if exists
if [ -d "/Applications/VibeReps.app" ]; then
    echo "   Removing old version..."
    rm -rf "/Applications/VibeReps.app"
fi

# Copy new version
cp -r "$APP_PATH" /Applications/

echo "   Done!"
echo ""

# Check Claude Code hooks configuration
echo "4. Checking Claude Code hooks configuration..."

configure_hooks() {
    if [ "$HAS_JQ" = false ]; then
        echo "   jq not installed - cannot auto-configure hooks"
        echo "   Install jq with: brew install jq"
        echo "   Then run this installer again, or manually configure hooks."
        return 1
    fi

    # Create .claude directory if needed
    mkdir -p "$HOME/.claude"

    # Create settings.json if it doesn't exist
    if [ ! -f "$CLAUDE_SETTINGS" ]; then
        echo '{}' > "$CLAUDE_SETTINGS"
    fi

    # Backup existing settings
    cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.backup"

    # Create the hooks configuration
    local HOOKS_CONFIG=$(cat <<EOF
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "$REPO_DIR/vibereps.py",
            "async": true
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$REPO_DIR/vibereps.py",
            "async": true
          }
        ]
      }
    ]
  }
}
EOF
)

    # Merge hooks into existing settings
    local MERGED=$(jq -s '.[0] * .[1]' "$CLAUDE_SETTINGS" <(echo "$HOOKS_CONFIG"))
    echo "$MERGED" > "$CLAUDE_SETTINGS"

    echo "   Hooks configured in $CLAUDE_SETTINGS"
    echo "   Backup saved to $CLAUDE_SETTINGS.backup"
    return 0
}

# Check if hooks are already configured
HOOKS_CONFIGURED=false
if [ -f "$CLAUDE_SETTINGS" ] && [ "$HAS_JQ" = true ]; then
    if jq -e '.hooks.PostToolUse' "$CLAUDE_SETTINGS" &>/dev/null; then
        # Check if vibereps hooks are configured
        if jq -e '.hooks.PostToolUse[].hooks[].command | contains("vibereps")' "$CLAUDE_SETTINGS" &>/dev/null; then
            HOOKS_CONFIGURED=true
            echo "   Claude Code hooks already configured!"
        fi
    fi
fi

if [ "$HOOKS_CONFIGURED" = false ]; then
    echo ""
    echo "   Claude Code hooks are not configured for VibeReps."
    echo ""
    read -p "   Would you like to configure hooks automatically? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if configure_hooks; then
            echo ""
            echo "   Hooks configured successfully!"
        fi
    else
        echo ""
        echo "   Skipping hooks configuration."
        echo "   You can manually add hooks to $CLAUDE_SETTINGS later."
    fi
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "VibeReps has been installed to /Applications/VibeReps.app"
echo ""
echo "To start the app:"
echo "  open /Applications/VibeReps.app"
echo ""
echo "To start at login:"
echo "  1. Open System Settings > General > Login Items"
echo "  2. Click '+' and add VibeReps"
echo ""

if [ "$HOOKS_CONFIGURED" = false ] && [ "$HAS_JQ" = false ]; then
    echo "To configure Claude Code hooks manually, add to $CLAUDE_SETTINGS:"
    cat <<EOF
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "$REPO_DIR/vibereps.py",
        "async": true
      }]
    }],
    "Notification": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "$REPO_DIR/vibereps.py",
        "async": true
      }]
    }]
  }
}
EOF
    echo ""
fi
