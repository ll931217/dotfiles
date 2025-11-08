#!/usr/bin/env python3
import i3ipc
import re
import subprocess

# Set your config file path
PICOM_CONFIG = "/home/ll931217/.config/picom.conf"


# Helper to read and update animation direction in picom.conf
def set_slide_direction(direction):
    with open(PICOM_CONFIG, "r") as f:
        config = f.read()
    # Change the direction in the animations block (left/right)
    new_config = re.sub(
        r'(direction = ")(left|right)(";)', f"\\1{direction}\\3", config
    )
    with open(PICOM_CONFIG, "w") as f:
        f.write(new_config)
    # Reload picom (works if started without --daemon)
    subprocess.run(["pkill", "-SIGUSR1", "picom"])


def on_workspace(i3, event):
    global previous_ws
    current_ws = event.current.num if event.current else None
    if previous_ws is None or current_ws is None:
        previous_ws = current_ws
        return
    if current_ws > previous_ws:
        set_slide_direction("left")  # 1 → 2 → 3 slides left
    elif current_ws < previous_ws:
        set_slide_direction("right")  # 3 → 2 → 1 slides right
    previous_ws = current_ws


if __name__ == "__main__":
    previous_ws = None
    i3 = i3ipc.Connection()
    ws_list = i3.get_workspaces()
    if ws_list:
        previous_ws = next((w.num for w in ws_list if w.focused), None)
    i3.on("workspace::focus", on_workspace)
    i3.main()
