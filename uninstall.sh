#!/bin/bash
# VibeReps Uninstaller for Claude Code

set -e

INSTALL_DIR="${VIBEREPS_DIR:-$HOME/.vibereps}"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🗑️  Uninstalling VibeReps..."

# Remove hooks from settings if jq is available
if command -v jq &> /dev/null && [ -f "$SETTINGS_FILE" ]; then
    TEMP_FILE=$(mktemp)
    jq 'del(.hooks.UserPromptSubmit) | del(.hooks.PostMessage)' "$SETTINGS_FILE" > "$TEMP_FILE"
    mv "$TEMP_FILE" "$SETTINGS_FILE"
    echo "⚙️  Removed hooks from settings"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "📦 Removed $INSTALL_DIR"
fi

echo "✅ VibeReps uninstalled successfully!"
echo "🔄 Restart Claude Code to complete removal."
