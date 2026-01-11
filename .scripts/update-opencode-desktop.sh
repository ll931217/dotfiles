#!/bin/bash

# OpenCode Desktop AppImage Updater Script
# Downloads the latest OpenCode AppImage and sets it up properly

set -e

# Configuration
OPENCODE_URL="https://opencode.ai/download/linux-x64-appimage"
APPS_DIR="$HOME/Applications"
DESKTOP_DIR="$HOME/.local/share/applications"
APPIMAGE_NAME="OpenCode.AppImage"
DESKTOP_FILE="$DESKTOP_DIR/OpenCode.desktop"

echo "🚀 Starting OpenCode update process..."

# Create Applications directory if it doesn't exist
if [ ! -d "$APPS_DIR" ]; then
  echo "📁 Creating $APPS_DIR directory..."
  mkdir -p "$APPS_DIR"
else
  echo "✅ Applications directory already exists"
fi

# Create .local/share/applications directory if it doesn't exist
if [ ! -d "$DESKTOP_DIR" ]; then
  echo "📁 Creating $DESKTOP_DIR directory..."
  mkdir -p "$DESKTOP_DIR"
else
  echo "✅ Desktop applications directory already exists"
fi

# Download the AppImage
echo "⬇️  Downloading OpenCode AppImage from $OPENCODE_URL..."
# Download to temp file first
TEMP_FILE="/tmp/opencode-appimage-$$"
curl -L -o "$TEMP_FILE" "$OPENCODE_URL"

# Move to Applications directory
echo "📦 Moving AppImage to $APPS_DIR..."
mv "$TEMP_FILE" "$APPS_DIR/$APPIMAGE_NAME"

# Make it executable
echo "🔐 Making AppImage executable..."
chmod +x "$APPS_DIR/$APPIMAGE_NAME"

# Create/update desktop file
echo "📝 Creating desktop entry at $DESKTOP_FILE..."
cat >"$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=OpenCode
Comment=OpenCode Desktop
Exec=$APPS_DIR/$APPIMAGE_NAME
Icon=opencode
Type=Application
Categories=Development;IDE;Utility;
Terminal=false
StartupNotify=true
EOF

echo "✅ OpenCode update completed successfully!"
echo ""
echo "📍 AppImage location: $APPS_DIR/$APPIMAGE_NAME"
echo "📍 Desktop file location: $DESKTOP_FILE"
echo ""
echo "You can now launch OpenCode from your application menu or run:"
echo "  $APPS_DIR/$APPIMAGE_NAME"
