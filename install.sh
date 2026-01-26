#!/bin/bash
#
# VibeReps Installer for Claude Code
# Test edit - exercise buttons should now collapse
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
RELEASE_URL="https://github.com/Flow-Club/vibereps/releases/latest/download/vibereps.tar.gz"
ELECTRON_DMG_URL="https://github.com/Flow-Club/vibereps/releases/latest/download/VibeReps.dmg"

# UI mode: electron or webapp (default: prompt user)
UI_MODE="${VIBEREPS_UI_MODE:-}"

# Trigger mode: prompt (experimental) or edit-only (default: prompt user)
TRIGGER_MODE="${VIBEREPS_TRIGGER_MODE:-}"

# Check if we're running from an existing clone/dev install
detect_local_install() {
    if [[ -f "$(dirname "${BASH_SOURCE[0]}")/exercise_tracker.py" ]]; then
        INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        return 0
    fi
    return 1
}

# Prompt user to choose UI mode
choose_ui_mode() {
    if [[ -n "$UI_MODE" ]]; then
        return 0
    fi

    echo ""
    echo -e "${BLUE}Choose your preferred UI:${NC}"
    echo ""
    echo -e "  ${YELLOW}1)${NC} ${GREEN}Menubar App${NC} (Recommended)"
    echo "     macOS (Electron) app that lives in your menu bar"
    echo "     Exercises appear in a small overlay window"
    echo "     More reliable window opening and notifications"
    echo ""
    echo -e "  ${YELLOW}2)${NC} ${GREEN}Web Browser${NC}"
    echo "     Opens in your default browser"
    echo "     No additional apps installed"
    echo "     Lighter weight, but less reliable window opening experience"
    echo ""

    while true; do
        read -p "Enter choice [1/2]: " -n 1 -r choice
        echo ""
        case "$choice" in
            1)
                UI_MODE="electron"
                print_success "Selected: Menubar App"
                break
                ;;
            2)
                UI_MODE="webapp"
                print_success "Selected: Web Browser"
                break
                ;;
            *)
                print_warning "Please enter 1 or 2"
                ;;
        esac
    done
    echo ""
}

# Prompt user to choose trigger mode
choose_trigger_mode() {
    if [[ -n "$TRIGGER_MODE" ]]; then
        return 0
    fi

    echo ""
    echo -e "${BLUE}When should exercises trigger?${NC}"
    echo ""
    echo -e "  ${YELLOW}1)${NC} ${GREEN}On File Edits${NC} (Recommended)"
    echo "     Exercises trigger when Claude edits/writes code"
    echo "     Most reliable - only triggers when actual changes happen"
    echo ""
    echo -e "  ${YELLOW}2)${NC} ${GREEN}On Prompt Submit${NC} (Experimental)"
    echo "     Exercises also trigger when you submit a prompt"
    echo "     Uses AI to guess if your prompt will result in edits"
    echo "     Triggers earlier, but may have false positives"
    echo ""

    while true; do
        read -p "Enter choice [1/2]: " -n 1 -r choice
        echo ""
        case "$choice" in
            1)
                TRIGGER_MODE="edit-only"
                print_success "Selected: On File Edits"
                break
                ;;
            2)
                TRIGGER_MODE="prompt"
                print_success "Selected: On Prompt Submit (Experimental)"
                break
                ;;
            *)
                print_warning "Please enter 1 or 2"
                ;;
        esac
    done
    echo ""
}

# Install Electron menubar app
install_electron_app() {
    print_step "Installing VibeReps Menubar App"

    # Check if running from local clone with electron directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -d "$SCRIPT_DIR/electron" ]] && [[ -f "$SCRIPT_DIR/electron/package.json" ]]; then
        print_step "Building from source..."

        # Check for Node.js
        if ! command -v node &> /dev/null; then
            print_error "Node.js is required to build the Electron app"
            echo "Install it from https://nodejs.org/ or via: brew install node"
            echo ""
            print_warning "Falling back to web browser mode..."
            UI_MODE="webapp"
            return 1
        fi

        # Build and install
        cd "$SCRIPT_DIR/electron"
        print_step "Installing npm dependencies..."
        npm install --silent 2>/dev/null || npm install

        print_step "Building app..."
        npm run build --silent 2>/dev/null || npm run build

        # Determine architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" = "arm64" ]]; then
            APP_PATH="dist/mac-arm64/VibeReps.app"
        else
            APP_PATH="dist/mac/VibeReps.app"
        fi

        if [[ ! -d "$APP_PATH" ]]; then
            print_error "Build failed - $APP_PATH not found"
            print_warning "Falling back to web browser mode..."
            UI_MODE="webapp"
            cd "$SCRIPT_DIR"
            return 1
        fi

        # Install to /Applications
        if [[ -d "/Applications/VibeReps.app" ]]; then
            print_step "Removing old version..."
            rm -rf "/Applications/VibeReps.app"
        fi

        cp -r "$APP_PATH" /Applications/
        print_success "Installed to /Applications/VibeReps.app"

        cd "$SCRIPT_DIR"
    else
        # Download pre-built DMG from releases
        print_step "Downloading VibeReps.dmg..."

        TEMP_DIR=$(mktemp -d)
        TEMP_DMG="$TEMP_DIR/VibeReps.dmg"
        if curl -sSL -o "$TEMP_DMG" "$ELECTRON_DMG_URL" 2>/dev/null; then
            print_success "Downloaded DMG"
        else
            print_error "Failed to download Electron app."
            print_warning "Falling back to web browser mode..."
            UI_MODE="webapp"
            return 1
        fi

        # Mount and copy
        print_step "Installing app..."
        MOUNT_POINT=$(mktemp -d)
        if hdiutil attach "$TEMP_DMG" -mountpoint "$MOUNT_POINT" -quiet 2>/dev/null; then
            if [[ -d "/Applications/VibeReps.app" ]]; then
                rm -rf "/Applications/VibeReps.app"
            fi

            cp -r "$MOUNT_POINT/VibeReps.app" /Applications/
            hdiutil detach "$MOUNT_POINT" -quiet
            rm -rf "$TEMP_DIR"

            print_success "Installed to /Applications/VibeReps.app"
        else
            print_error "Failed to mount DMG"
            print_warning "Falling back to web browser mode..."
            rm -rf "$TEMP_DIR"
            UI_MODE="webapp"
            return 1
        fi
    fi

    return 0
}

# Install or update vibereps (webapp version)
install_vibereps() {
    if detect_local_install; then
        print_step "Using local installation at $INSTALL_DIR"
        return 0
    fi

    print_step "Downloading VibeReps"

    # Preserve user data (exercise logs)
    USER_DATA_FILE="$INSTALL_DIR/exercises.jsonl"
    if [[ -f "$USER_DATA_FILE" ]]; then
        BACKUP_DATA=$(mktemp)
        cp "$USER_DATA_FILE" "$BACKUP_DATA"
        print_step "Preserving existing exercise log"
    fi

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Download and extract tarball
    if curl -sSL "$RELEASE_URL" | tar -xz -C "$INSTALL_DIR" 2>/dev/null; then
        print_success "Downloaded and extracted to $INSTALL_DIR"
    else
        print_error "Failed to download release. Check your internet connection."
        # Restore user data on failure
        [[ -n "${BACKUP_DATA:-}" ]] && mv "$BACKUP_DATA" "$USER_DATA_FILE"
        exit 1
    fi

    # Restore user data
    if [[ -n "${BACKUP_DATA:-}" ]]; then
        mv "$BACKUP_DATA" "$USER_DATA_FILE"
        print_success "Restored exercise log"
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
trigger_mode = "$TRIGGER_MODE"

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
            "matcher": "idle_prompt|permission_prompt",
            "hooks": [
                {
                    "type": "command",
                    "command": f"{install_dir}/notify_complete.py '{{}}'"
                }
            ]
        }
    ]
}

# Add experimental prompt detection hook if enabled
if trigger_mode == "prompt":
    vibereps_hooks["UserPromptSubmit"] = [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches {install_dir}/exercise_tracker.py user_prompt_submit '{{}}'"
                }
            ]
        }
    ]

# Remove any existing vibereps hooks first, then add new ones
for hook_type, hook_configs in vibereps_hooks.items():
    if hook_type not in settings["hooks"]:
        settings["hooks"][hook_type] = []

    # Filter out old vibereps hooks
    def is_vibereps_hook(h):
        if isinstance(h, dict):
            if "exercise_tracker.py" in str(h) or "notify_complete.py" in str(h):
                return True
            if "hooks" in h:
                for nested in h["hooks"]:
                    if isinstance(nested, dict) and ("exercise_tracker.py" in str(nested) or "notify_complete.py" in str(nested)):
                        return True
        return False

    settings["hooks"][hook_type] = [h for h in settings["hooks"][hook_type] if not is_vibereps_hook(h)]

    # Add the new hooks
    for hook_config in hook_configs:
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

    if [[ "$UI_MODE" == "electron" ]]; then
        echo -e "  ${BLUE}UI Mode:${NC} Menubar App"
        echo -e "  ${BLUE}App location:${NC} /Applications/VibeReps.app"
    else
        echo -e "  ${BLUE}UI Mode:${NC} Web Browser"
    fi
    if [[ "$TRIGGER_MODE" == "prompt" ]]; then
        echo -e "  ${BLUE}Trigger Mode:${NC} On Prompt Submit (Experimental)"
    else
        echo -e "  ${BLUE}Trigger Mode:${NC} On File Edits"
    fi
    echo -e "  ${BLUE}Scripts location:${NC} $INSTALL_DIR"
    echo ""
    echo -e "  ${GREEN}Next steps:${NC}"
    echo ""

    if [[ "$UI_MODE" == "electron" ]]; then
        echo -e "    ${YELLOW}1.${NC} Launch the menubar app:"
        echo "       open /Applications/VibeReps.app"
        echo ""
        echo -e "    ${YELLOW}2.${NC} (Optional) Start at login:"
        echo "       System Settings → General → Login Items → Add VibeReps"
        echo ""
        echo -e "    ${YELLOW}3.${NC} Restart Claude Code"
    else
        echo -e "    ${YELLOW}1.${NC} Restart Claude Code"
    fi
    echo ""
    if [[ "$TRIGGER_MODE" == "prompt" ]]; then
        echo -e "  ${BLUE}Hooks:${NC} ✓ Configured (exercises trigger on prompts + file edits)"
    else
        echo -e "  ${BLUE}Hooks:${NC} ✓ Configured (exercises trigger on file edits)"
    fi
    echo ""
    echo -e "  ${BLUE}Customize exercises (optional):${NC}"
    echo -e "    Run ${GREEN}/setup-vibereps${NC} in Claude Code to change exercise types"
    echo ""
    echo -e "  ${BLUE}How it works:${NC}"
    if [[ "$TRIGGER_MODE" == "prompt" ]]; then
        if [[ "$UI_MODE" == "electron" ]]; then
            echo "    You submit a prompt → AI guesses if edits likely → Exercises start"
            echo "    → Claude finishes → App notifies you → You return"
        else
            echo "    You submit a prompt → AI guesses if edits likely → Browser opens"
            echo "    → Claude finishes → Desktop notification → You return"
        fi
    else
        if [[ "$UI_MODE" == "electron" ]]; then
            echo "    Claude edits a file → Menubar app shows exercises → You exercise"
            echo "    → Claude finishes → App notifies you → You return"
        else
            echo "    Claude edits a file → Browser opens → You exercise"
            echo "    → Claude finishes → Desktop notification → You return"
        fi
    fi
    echo ""
    echo -e "  ${BLUE}Other commands:${NC}"
    echo "    /test-tracker    - Test the exercise tracker"
    echo "    /add-exercise    - Create a custom exercise"
    echo "    /tune-detection  - Adjust detection sensitivity"
    echo ""
    echo -e "  ${BLUE}To uninstall:${NC} $INSTALL_DIR/install.sh --uninstall"
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

    # Remove Electron app if installed
    if [[ -d "/Applications/VibeReps.app" ]]; then
        read -p "Remove /Applications/VibeReps.app? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "/Applications/VibeReps.app"
            print_success "Removed /Applications/VibeReps.app"
        fi
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
        echo "  VIBEREPS_UI_MODE        UI mode: 'electron' or 'webapp' (default: prompt)"
        echo "  VIBEREPS_TRIGGER_MODE   Trigger mode: 'edit-only' or 'prompt' (default: prompt user)"
        echo "                          'edit-only' = trigger on file edits only (recommended)"
        echo "                          'prompt' = also trigger on prompt submit (experimental)"
        echo ""
        echo "Examples:"
        echo "  # Install from GitHub (interactive)"
        echo "  curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash"
        echo ""
        echo "  # Install menubar app non-interactively"
        echo "  VIBEREPS_UI_MODE=electron VIBEREPS_TRIGGER_MODE=edit-only ./install.sh"
        echo ""
        echo "  # Install with experimental prompt detection"
        echo "  VIBEREPS_TRIGGER_MODE=prompt ./install.sh"
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

# Ask user for preferences
choose_ui_mode
choose_trigger_mode

# Install based on choice
if [[ "$UI_MODE" == "electron" ]]; then
    if install_electron_app; then
        # Electron install succeeded, still need webapp files for hooks
        install_vibereps
    else
        # Fallback happened, UI_MODE is now webapp
        install_vibereps
    fi
else
    install_vibereps
fi

setup_permissions
backup_settings
configure_hooks
show_summary
