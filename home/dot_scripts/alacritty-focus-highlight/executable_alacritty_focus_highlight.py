#!/usr/bin/env python3
"""
Alacritty Focus Highlight Daemon

Brightens the background color of focused Alacritty windows using i3ipc events
and per-window IPC configuration.
"""

import os
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Optional

import i3ipc


class AlacrittyFocusHighlight:
    """Manages focus-based color highlighting for Alacritty windows."""

    def __init__(self, config_path: Path):
        """Initialize the daemon with configuration."""
        self.config = self._load_config(config_path)
        self.base_color = self.config["colors"]["base"]
        self.brightness_pct = self.config["highlight"]["brightness_percentage"]

        # Track state: {window_id: {"original_color": str, "socket": Path}}
        self.focused_windows = {}
        self.previous_focus = None

    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from TOML file with fallback defaults."""
        default_config = {
            "colors": {"base": "#101010"},
            "highlight": {"brightness_percentage": 0.15}
        }

        if not config_path.exists():
            return default_config

        try:
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return default_config

    def brighten_color(self, hex_color: str, percentage: float) -> str:
        """
        Brighten a hex color by a percentage.

        Args:
            hex_color: Hex color string like "#101010"
            percentage: Brightness increase (0.0 to 1.0, e.g., 0.15 = 15% brighter)

        Returns:
            Brightened hex color string
        """
        # Remove '#' and parse RGB
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Brighten by moving toward white (255)
        r = min(255, int(r + (255 - r) * percentage))
        g = min(255, int(g + (255 - g) * percentage))
        b = min(255, int(b + (255 - b) * percentage))

        return f"#{r:02x}{g:02x}{b:02x}"

    def get_window_pid(self, window_id: int) -> Optional[int]:
        """
        Get the PID of a window using xprop.

        Args:
            window_id: X11 window ID

        Returns:
            Process ID or None if not found
        """
        try:
            result = subprocess.run(
                ["/usr/bin/xprop", "-id", str(window_id), "_NET_WM_PID"],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "_NET_WM_PID(CARDINAL) = 12345"
            if "=" in result.stdout:
                return int(result.stdout.split("=")[1].strip())
        except (subprocess.CalledProcessError, ValueError, IndexError):
            pass
        return None

    def _find_socket_once(self, pid: int) -> Optional[Path]:
        """
        Attempt to find the Alacritty IPC socket once (without retry).

        Socket path format: /run/user/<UID>/Alacritty-<DISPLAY>-<PID>.sock

        Args:
            pid: Process ID of Alacritty instance

        Returns:
            Path to socket file or None if not found
        """
        uid = os.getuid()
        display = os.environ.get("DISPLAY", ":0")

        socket_path = Path(f"/run/user/{uid}/Alacritty-{display}-{pid}.sock")

        if socket_path.exists():
            return socket_path

        # Fallback: search for any socket matching the PID
        run_dir = Path(f"/run/user/{uid}")
        if run_dir.exists():
            for socket in run_dir.glob(f"Alacritty-*-{pid}.sock"):
                return socket

        return None

    def find_alacritty_socket(self, pid: int, max_retries: int = 5, delay: float = 0.1) -> Optional[Path]:
        """
        Find the Alacritty IPC socket for a given PID with retry logic.

        This handles the race condition when new Alacritty windows are created
        and the socket may not exist yet when the focus event fires.

        Args:
            pid: Process ID of Alacritty instance
            max_retries: Maximum number of attempts (default: 5)
            delay: Delay between retries in seconds (default: 0.1)

        Returns:
            Path to socket file or None if not found after all retries
        """
        for attempt in range(max_retries):
            socket = self._find_socket_once(pid)
            if socket:
                return socket
            if attempt < max_retries - 1:
                time.sleep(delay)

        return None

    def send_alacritty_color(self, socket: Path, color: str, window_id: int) -> bool:
        """
        Send color configuration to Alacritty via IPC.

        Args:
            socket: Path to Alacritty IPC socket
            color: Hex color string
            window_id: X11 window ID to apply config to

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                [
                    "alacritty",
                    "msg",
                    "--socket", str(socket),
                    "config",
                    "--window-id", str(window_id),
                    f"colors.primary.background='{color}'"
                ],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def on_window_focus(self, i3: i3ipc.Connection, event: i3ipc.Event):
        """
        Handle i3 window focus events.

        When an Alacritty window gains focus, brighten its background.
        When focus leaves an Alacritty window, restore original background.
        """
        window = event.container
        window_id = window.window

        # Restore previous window color if it was Alacritty
        if self.previous_focus and self.previous_focus in self.focused_windows:
            prev_state = self.focused_windows[self.previous_focus]
            self.send_alacritty_color(
                prev_state["socket"],
                prev_state["original_color"],
                self.previous_focus
            )
            del self.focused_windows[self.previous_focus]

        # Check if new focus is Alacritty
        if window.window_class == "Alacritty":
            pid = self.get_window_pid(window_id)
            if not pid:
                self.previous_focus = window_id
                return

            socket = self.find_alacritty_socket(pid)
            if not socket:
                self.previous_focus = window_id
                return

            # Store state and apply brightened color
            bright_color = self.brighten_color(self.base_color, self.brightness_pct)
            self.focused_windows[window_id] = {
                "original_color": self.base_color,
                "socket": socket
            }
            self.send_alacritty_color(socket, bright_color, window_id)

        self.previous_focus = window_id

    def on_window_close(self, i3: i3ipc.Connection, event: i3ipc.Event):
        """
        Handle window close events to cleanup state.

        Remove closed windows from tracking to prevent memory leaks.
        """
        window_id = event.container.window
        if window_id in self.focused_windows:
            del self.focused_windows[window_id]
        if self.previous_focus == window_id:
            self.previous_focus = None

    def highlight_current_focus(self, i3: i3ipc.Connection):
        """Highlight the currently focused window on startup."""
        focused = i3.get_tree().find_focused()
        if focused and focused.window_class == "Alacritty":
            window_id = focused.window

            pid = self.get_window_pid(window_id)
            if pid:
                socket = self.find_alacritty_socket(pid)
                if socket:
                    bright_color = self.brighten_color(self.base_color, self.brightness_pct)
                    self.focused_windows[window_id] = {
                        "original_color": self.base_color,
                        "socket": socket
                    }
                    self.send_alacritty_color(socket, bright_color, window_id)
                    self.previous_focus = window_id

    def run(self):
        """Start the daemon and listen for i3 events."""
        i3 = i3ipc.Connection()

        # Subscribe to focus and close events
        i3.on(i3ipc.Event.WINDOW_FOCUS, self.on_window_focus)
        i3.on(i3ipc.Event.WINDOW_CLOSE, self.on_window_close)

        # Highlight the currently focused window immediately
        self.highlight_current_focus(i3)

        # Start event loop
        i3.main()


def main():
    """Entry point for the daemon."""
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.toml"

    daemon = AlacrittyFocusHighlight(config_path)
    daemon.run()


if __name__ == "__main__":
    main()
