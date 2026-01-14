#!/bin/bash
#
# VibeReps Installer for Claude Code
# One-liner install: curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() { echo -e "${BLUE}==>${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}!${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Default install location
INSTALL_DIR="${VIBEREPS_INSTALL_DIR:-$HOME/.vibereps}"
SETTINGS_FILE="$HOME/.claude/settings.json"
REPO_URL="https://github.com/Flow-Club/vibereps.git"

# Check if we're running from an existing clone
detect_local_install() {
    if [[ -f "$(dirname "${BASH_SOURCE[0]}")/exercise_tracker.py" ]]; then
        INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        return 0
    fi
    return 1
}

# Install or update vibereps
install_vibereps() {
    if detect_local_install; then
        print_step "Using existing installation at $INSTALL_DIR"
    elif [[ -d "$INSTALL_DIR" ]]; then
        print_step "Updating existing installation at $INSTALL_DIR"
        cd "$INSTALL_DIR"
        git pull origin main 2>/dev/null || git pull 2>/dev/null || print_warning "Could not update, using existing files"
    else
        print_step "Installing VibeReps to $INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
}

# Make scripts executable
setup_permissions() {
    print_step "Setting up permissions"
    chmod +x "$INSTALL_DIR/exercise_tracker.py"
    chmod +x "$INSTALL_DIR/notify_complete.py"
    print_success "Scripts are executable"
}

# Backup existing settings
backup_settings() {
    if [[ -f "$SETTINGS_FILE" ]]; then
        BACKUP_FILE="${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$SETTINGS_FILE" "$BACKUP_FILE"
        print_success "Backed up existing settings to $BACKUP_FILE"
    fi
}

# Configure Claude Code hooks using Python for JSON manipulation
configure_hooks() {
    print_step "Configuring Claude Code hooks"

    # Ensure .claude directory exists
    mkdir -p "$HOME/.claude"

    # Use Python for reliable JSON manipulation
    python3 << PYTHON_SCRIPT
import json
import os
from pathlib import Path

settings_file = Path("$SETTINGS_FILE")
install_dir = "$INSTALL_DIR"

# Load existing settings or create empty
if settings_file.exists():
    try:
        with open(settings_file) as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        settings = {}
else:
    settings = {}

# Ensure hooks structure exists
if "hooks" not in settings:
    settings["hooks"] = {}

# Define the vibereps hooks
vibereps_hooks = {
    "PostToolUse": [
        {
            "matcher": "Write|Edit|MultiEdit",
            "hooks": [
                {
                    "type": "command",
                    "command": f"VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches {install_dir}/exercise_tracker.py post_tool_use '{{}}'"
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
                    "command": f"{install_dir}/notify_complete.py '{{}}'"
                }
            ]
        }
    ]
}

# Add vibereps hooks (preserving existing hooks)
for hook_type, hook_configs in vibereps_hooks.items():
    if hook_type not in settings["hooks"]:
        settings["hooks"][hook_type] = []

    # Check if vibereps hook already exists
    existing_commands = [
        h.get("command", "") if isinstance(h, dict) else ""
        for h in settings["hooks"][hook_type]
    ]
    # Also check nested hooks
    for h in settings["hooks"][hook_type]:
        if isinstance(h, dict) and "hooks" in h:
            for nested in h["hooks"]:
                if isinstance(nested, dict):
                    existing_commands.append(nested.get("command", ""))

    for hook_config in hook_configs:
        # Check if this hook's command already exists
        if isinstance(hook_config, dict) and "hooks" in hook_config:
            cmd = hook_config["hooks"][0].get("command", "")
        else:
            cmd = hook_config.get("command", "")

        if not any("exercise_tracker.py" in c or "notify_complete.py" in c for c in existing_commands):
            settings["hooks"][hook_type].append(hook_config)

# Write updated settings
with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)

print("Hooks configured successfully")
PYTHON_SCRIPT

    print_success "Claude Code hooks configured"
}

# Show summary
show_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}           ${GREEN}VibeReps installed successfully!${NC}               ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BLUE}Install location:${NC} $INSTALL_DIR"
    echo -e "  ${BLUE}Settings file:${NC}    $SETTINGS_FILE"
    echo ""
    echo -e "  ${YELLOW}How it works:${NC}"
    echo "    1. Claude edits a file → Exercise tracker launches"
    echo "    2. Do 5 quick exercises while Claude works"
    echo "    3. Get notified when Claude is ready!"
    echo ""
    echo -e "  ${YELLOW}Next steps:${NC}"
    echo "    • Restart Claude Code to activate hooks"
    echo "    • Grant camera permission when prompted"
    echo "    • Run /setup-vibereps in Claude Code to customize exercises"
    echo ""
    echo -e "  ${YELLOW}Test it now:${NC}"
    echo "    $INSTALL_DIR/exercise_tracker.py post_tool_use '{}'"
    echo ""
    echo -e "  ${YELLOW}See available exercises:${NC}"
    echo "    $INSTALL_DIR/exercise_tracker.py --list-exercises"
    echo ""
    echo -e "  ${YELLOW}Optional - Customize exercises (add to ~/.bashrc or ~/.zshrc):${NC}"
    echo "    export VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches"
    echo ""
    echo -e "  ${YELLOW}To uninstall:${NC}"
    echo "    $INSTALL_DIR/install.sh --uninstall"
    echo ""
}

# Uninstall vibereps
uninstall() {
    print_step "Uninstalling VibeReps"

    # Remove hooks from settings using Python
    if [[ -f "$SETTINGS_FILE" ]]; then
        python3 << PYTHON_SCRIPT
import json
from pathlib import Path

settings_file = Path("$SETTINGS_FILE")

if settings_file.exists():
    with open(settings_file) as f:
        settings = json.load(f)

    if "hooks" in settings:
        for hook_type in list(settings["hooks"].keys()):
            # Filter out vibereps hooks
            settings["hooks"][hook_type] = [
                h for h in settings["hooks"][hook_type]
                if not (
                    ("exercise_tracker.py" in str(h)) or
                    ("notify_complete.py" in str(h)) or
                    ("vibereps" in str(h).lower())
                )
            ]
            # Remove empty hook types
            if not settings["hooks"][hook_type]:
                del settings["hooks"][hook_type]

        # Remove empty hooks object
        if not settings["hooks"]:
            del settings["hooks"]

    with open(settings_file, "w") as f:
        json.dump(settings, f, indent=2)

    print("Hooks removed from settings")
PYTHON_SCRIPT
        print_success "Removed hooks from Claude Code settings"
    fi

    # Optionally remove install directory
    if [[ -d "$INSTALL_DIR" ]] && [[ "$INSTALL_DIR" == "$HOME/.vibereps" ]]; then
        read -p "Remove $INSTALL_DIR? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            print_success "Removed $INSTALL_DIR"
        fi
    fi

    echo ""
    print_success "VibeReps uninstalled. Restart Claude Code to apply changes."
}

# Parse arguments
case "${1:-}" in
    --uninstall|-u)
        uninstall
        exit 0
        ;;
    --help|-h)
        echo "VibeReps Installer"
        echo ""
        echo "Usage: install.sh [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --uninstall, -u    Remove VibeReps from Claude Code"
        echo "  --help, -h         Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  VIBEREPS_INSTALL_DIR    Custom install directory (default: ~/.vibereps)"
        echo ""
        echo "Examples:"
        echo "  # Install from GitHub"
        echo "  curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash"
        echo ""
        echo "  # Install to custom directory"
        echo "  VIBEREPS_INSTALL_DIR=/opt/vibereps ./install.sh"
        echo ""
        echo "  # Uninstall"
        echo "  ~/.vibereps/install.sh --uninstall"
        exit 0
        ;;
esac

# Main installation
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}                    ${BLUE}VibeReps Installer${NC}                      ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}       Don't neglect your physical corpus!                  ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

install_vibereps
setup_permissions
backup_settings
configure_hooks
show_summary
