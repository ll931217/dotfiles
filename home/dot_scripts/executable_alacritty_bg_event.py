#!/usr/bin/env python3
"""
Event-driven Alacritty background color manager.
Changes background color based on i3 window focus.
"""

import os
import sys
import subprocess
import i3ipc

# Ensure output is unbuffered
sys.stdout.reconfigure(line_buffering=True)

ACTIVE_BG = "#1A1A20"
INACTIVE_BG = "#101010"

class Manager:
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.sockets = {}  # X11 ID -> socket
        self.focused_x11_id = None
        self._log("Initializing...")
        self._build_map()
    
    def _log(self, message):
        """Log message with newline and flush."""
        sys.stdout.write(message + "\n")
        sys.stdout.flush()
    
    def _build_map(self):
        """Map X11 window IDs to Alacritty sockets."""
        self.sockets = {}
        count = 0
        for pid in [d for d in os.listdir("/proc") if d.isdigit()]:
            try:
                # Check if it's a zsh process
                with open("/proc/" + pid + "/comm") as f:
                    if f.read().strip() != "zsh":
                        continue
                
                # Get parent PID
                ppid = subprocess.check_output(["ps", "-o", "ppid=", "-p", pid]).decode().strip()
                
                # Check if parent is alacritty
                with open("/proc/" + ppid + "/comm") as f:
                    if f.read().strip() != "alacritty":
                        continue
                
                # Get ALACRITTY_WINDOW_ID from environment
                with open("/proc/" + pid + "/environ", "rb") as f:
                    for line in f.read().split(b"\x00"):
                        if line.startswith(b"ALACRITTY_WINDOW_ID="):
                            x11_id = line.split(b"=")[1].decode()
                            # Build socket path
                            sock = f"/run/user/1000/Alacritty-:0-{ppid}.sock"
                            if os.path.exists(sock):
                                self.sockets[x11_id] = sock
                                count += 1
                                self._log(f"  Found window {x11_id} on socket {ppid}")
            except:
                pass
        
        self._log(f"Mapped {count} Alacritty windows")
    
    def set_bg(self, x11_id, active):
        """Set background color for a window."""
        if x11_id not in self.sockets:
            return
        
        sock = self.sockets[x11_id]
        color = ACTIVE_BG if active else INACTIVE_BG
        
        env = os.environ.copy()
        env["ALACRITTY_SOCKET"] = sock
        
        # Use -w -1 to apply to the socket's window
        cmd = ["alacritty", "msg", "config", "-w", "-1", f'colors.primary.background="{color}"']
        subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def set_initial_colors(self):
        """Set initial colors based on current focus."""
        # Get the focused window's X11 ID
        focused = self.i3.get_tree().find_focused()
        focused_x11 = str(focused.window) if focused else None
        
        self._log(f"Initial focused window: {focused_x11}")
        
        # Update each window
        for x11_id in self.sockets:
            active = (x11_id == focused_x11)
            self.set_bg(x11_id, active)
            status = "ACTIVE" if active else "inactive"
            self._log(f"  Window {x11_id}: {status} -> {ACTIVE_BG if active else INACTIVE_BG}")
    
    def on_focus(self, i3, e):
        """Handle window focus changes."""
        if not e.container:
            return
        
        new_focused = str(e.container.window)
        
        # Only log if focus changed to a different Alacritty window
        if new_focused in self.sockets and new_focused != self.focused_x11_id:
            self._log(f"Focus changed to Alacritty window {new_focused}")
            
            # Set old focused window to inactive
            if self.focused_x11_id and self.focused_x11_id in self.sockets:
                self.set_bg(self.focused_x11_id, False)
                self._log(f"  Window {self.focused_x11_id}: inactive")
            
            # Set new focused window to active
            self.set_bg(new_focused, True)
            self._log(f"  Window {new_focused}: active")
            
            self.focused_x11_id = new_focused
        elif new_focused not in self.sockets and self.focused_x11_id in self.sockets:
            # Focus moved away from Alacritty
            self.set_bg(self.focused_x11_id, False)
            self._log(f"Focus moved away from Alacritty, window {self.focused_x11_id}: inactive")
            self.focused_x11_id = None
    
    def run(self):
        """Start the event loop."""
        # Subscribe to window focus events
        self.i3.on("window::focus", self.on_focus)
        
        # Get initial focused window
        focused = self.i3.get_tree().find_focused()
        if focused:
            self.focused_x11_id = str(focused.window)
        
        self._log("Event-driven Alacritty background manager started")
        
        # Set initial state
        self.set_initial_colors()
        
        self._log("Listening for focus events (Ctrl+C to stop)...")
        self._log("=" * 50)
        
        # Main event loop
        try:
            self.i3.main()
        except KeyboardInterrupt:
            self._log("\nShutting down...")

if __name__ == "__main__":
    Manager().run()
