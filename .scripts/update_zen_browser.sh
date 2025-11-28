#!/bin/bash

# Simple Zen Browser AppImage Installer

# Get the latest release download URL
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/zen-browser/desktop/releases/latest |
    grep -o '"browser_download_url": *"[^"]*zen-x86_64\.AppImage"' |
    sed 's/"browser_download_url": *"//' | sed 's/"//')

# Create Applications directory
mkdir -p ~/Applications

# Download directly with the correct name, make executable, and move
cd /tmp
curl -L -o zen-browser.AppImage "$DOWNLOAD_URL"
chmod +x zen-browser.AppImage
mv zen-browser.AppImage ~/Applications/

echo "Zen Browser AppImage installed to ~/Applications/zen-browser.AppImage"
