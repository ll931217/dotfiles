#!/usr/bin/env python3
"""
Dynamic left border for Alacritty in i3wm.
Adjusts right padding when Alacritty is focused to create a left border effect.
Uses Alacritty's IPC for live config reload.
"""
import subprocess
import time
import json
import os
import sys
from i3ipc import Connection

# Configuration
ALACRITTY_CONFIG = os.path.expanduser("~/.config/alacritty/alacritty.toml")
BACKUP_CONFIG = os.path.expanduser("~/.config/alacritty/alacritty.toml.backup")
LOG_FILE = os.path.expanduser("~/.scripts/alacritty_border.log")
ALACRITTY_CLASS = "Alacritty"
ALACRITTY_SOCKET = os.environ.get("ALACRITTY_SOCKET")

# Padding values (in pixels)
NORMAL_PADDING_X = 14
FOCUSED_PADDING_X = 30  # Increased on the right to simulate left border

def log(message):
    """Write message to log file and stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')
        f.flush()

def load_config():
    """Load the current alacritty config."""
    try:
        with open(ALACRITTY_CONFIG, 'r') as f:
            return f.read()
    except Exception as e:
        log(f"Error loading config: {e}")
        return None

def save_config(content):
    """Save the alacritty config."""
    try:
        with open(ALACRITTY_CONFIG, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        log(f"Error saving config: {e}")
        return False

def backup_config():
    """Create a backup of the current config if it doesn't exist."""
    if not os.path.exists(BACKUP_CONFIG):
        import shutil
        shutil.copy(ALACRITTY_CONFIG, BACKUP_CONFIG)
        log(f"Created backup at {BACKUP_CONFIG}")

def update_padding(focused):
    """Update the padding.x value in the config."""
    content = load_config()
    if not content:
        return False
    
    # Calculate the desired padding
    if focused:
        new_padding = FOCUSED_PADDING_X
    else:
        new_padding = NORMAL_PADDING_X
    
    # Replace padding.x value
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if line.strip().startswith('padding.x'):
            # Preserve the indentation
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + f'padding.x = {new_padding}'
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    # Only write if changed
    if new_content != content:
        if save_config(new_content):
            log(f"{'Focused' if focused else 'Unfocused'} - Set padding.x to {new_padding}")
            # Try to reload Alacritty config
            reload_alacritty_config()
            return True
        else:
            return False
    else:
        log(f"No change needed (padding.x already {new_padding})")
        return False

def reload_alacritty_config():
    """Reload Alacritty configuration by sending a keybinding."""
    try:
        # Send Ctrl+Shift+R to reload config (you'll need to bind this in Alacritty)
        # Alternative: use xdotool to send the reload signal
        result = subprocess.run(
            ['xdotool', 'search', '--class', 'Alacritty', 'key', '--window', '%1', 'ctrl+shift+r'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            log("Sent reload signal to Alacritty")
            return True
        else:
            log(f"Failed to send reload signal: {result.stderr.decode()}")
            return False
    except FileNotFoundError:
        log("xdotool not found - install it with: sudo pacman -S xdotool")
        return False
    except Exception as e:
        log(f"Error reloading Alacritty config: {e}")
        return False

def is_alacritty_focused(i3):
    """Check if Alacritty is currently focused."""
    try:
        tree = i3.get_tree()
        focused = tree.find_focused()
        
        if focused:
            window_class = focused.window_class
            log(f"Focused window class: {window_class}")
            return window_class == ALACRITTY_CLASS
        else:
            log("No focused window found")
            return False
    except Exception as e:
        log(f"Error checking focus: {e}")
        return False

def on_focus(i3, e):
    """Handle focus events."""
    log(f"Window event: {e.change} (container={e.container})")
    
    # Check if the newly focused window is Alacritty
    if e.change == 'focus':
        focused = is_alacritty_focused(i3)
        log(f"Alacritty focused: {focused}")
        update_padding(focused)

def main():
    """Main function to run the border effect."""
    log("=" * 60)
    log("Starting Alacritty left border effect...")
    log(f"Config file: {ALACRITTY_CONFIG}")
    log(f"Focused padding: {FOCUSED_PADDING_X}px")
    log(f"Normal padding: {NORMAL_PADDING_X}px")
    log(f"Log file: {LOG_FILE}")
    log("Press Ctrl+C to stop")
    log("=" * 60)
    
    i3 = Connection()
    
    # Check initial state
    log("Checking initial focus state...")
    focused = is_alacritty_focused(i3)
    log(f"Initial state - Alacritty focused: {focused}")
    update_padding(focused)
    
    # Subscribe to focus events
    i3.on('window', on_focus)
    log("Subscribed to window events")
    
    # Main loop
    try:
        i3.main()
    except KeyboardInterrupt:
        log("\nStopping Alacritty left border effect...")
        # Restore normal padding on exit
        update_padding(False)
        log("Restored normal padding")

if __name__ == '__main__':
    import shutil
    try:
        main()
    except Exception as e:
        log(f"Fatal error: {e}")
        sys.exit(1)
