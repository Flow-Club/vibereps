#!/bin/bash
#
# Build release tarball for vibereps
# Creates vibereps.tar.gz with only the files needed for installation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/dist"
TARBALL_NAME="vibereps.tar.gz"

echo "Building vibereps release tarball..."

# Clean and create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Files to include in release
FILES=(
    "exercise_tracker.py"
    "notify_complete.py"
    "exercise_ui.html"
    "install.sh"
)

# Copy individual files
for file in "${FILES[@]}"; do
    cp "$PROJECT_ROOT/$file" "$BUILD_DIR/"
    echo "  Added $file"
done

# Copy exercises directory
cp -r "$PROJECT_ROOT/exercises" "$BUILD_DIR/"
echo "  Added exercises/"

# Copy assets (favicons, icons - excluding large non-essential files)
mkdir -p "$BUILD_DIR/assets"
for file in "$PROJECT_ROOT/assets/"*; do
    filename=$(basename "$file")
    # Skip large non-essential files
    if [[ "$filename" == "xkcd_waiting_for_claude.png" ]]; then
        continue
    fi
    cp "$file" "$BUILD_DIR/assets/"
done
echo "  Added assets/ (favicons and icons)"

# Create tarball (files at root level, not in subdirectory)
cd "$BUILD_DIR"
tar -czf "$TARBALL_NAME" *

echo ""
echo "Created: dist/$TARBALL_NAME"
echo "Contents:"
tar -tzf "$BUILD_DIR/$TARBALL_NAME" | head -20
echo ""
echo "Upload this to GitHub Releases"
