#!/bin/bash
# VibeReps Installer for Claude Code
# Usage: curl -fsSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash

set -e

INSTALL_DIR="${VIBEREPS_DIR:-$HOME/.vibereps}"
REPO_URL="https://github.com/Flow-Club/vibereps.git"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "🏋️ Installing VibeReps for Claude Code..."

# Clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --quiet
else
    echo "📦 Cloning VibeReps..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# Make scripts executable
chmod +x "$INSTALL_DIR/exercise_tracker.py"
chmod +x "$INSTALL_DIR/notify_complete.py"

# Create .claude directory if needed
mkdir -p "$HOME/.claude"

# Check if settings.json exists
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{}' > "$SETTINGS_FILE"
fi

# Check if jq is available for JSON manipulation
if command -v jq &> /dev/null; then
    echo "⚙️  Configuring Claude Code hooks..."

    # Create temp file with updated settings
    TEMP_FILE=$(mktemp)

    jq --arg tracker "$INSTALL_DIR/exercise_tracker.py" \
       --arg notifier "$INSTALL_DIR/notify_complete.py" '
       .hooks.UserPromptSubmit = [{"type": "command", "command": ($tracker + " user_prompt_submit '\''{}'\''")}] |
       .hooks.PostMessage = [{"type": "command", "command": ($notifier + " '\''{}'\''")}]
    ' "$SETTINGS_FILE" > "$TEMP_FILE"

    mv "$TEMP_FILE" "$SETTINGS_FILE"

    echo "✅ VibeReps installed successfully!"
    echo ""
    echo "🎯 Quick exercises will launch when you submit prompts."
    echo "📍 Installed to: $INSTALL_DIR"
    echo ""
    echo "Optional: Set up remote tracking:"
    echo "  export VIBEREPS_API_URL=https://your-server.com"
    echo "  export VIBEREPS_API_KEY=your_api_key"
else
    echo ""
    echo "⚠️  jq not found. Please manually add to $SETTINGS_FILE:"
    echo ""
    cat << EOF
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "$INSTALL_DIR/exercise_tracker.py user_prompt_submit '{}'"
      }
    ],
    "PostMessage": [
      {
        "type": "command",
        "command": "$INSTALL_DIR/notify_complete.py '{}'"
      }
    ]
  }
}
EOF
    echo ""
    echo "📍 Installed to: $INSTALL_DIR"
fi

echo ""
echo "🚀 Restart Claude Code to activate VibeReps!"
