#!/usr/bin/env python3
"""Network panel state and explicit user actions; passwords stay in native agents."""

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

HELPER = "/usr/local/libexec/eww-network-preference"
AGENT = "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1"


def run(*args, timeout=8):
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, check=False
    )


def state():
    result = {
        "available": False,
        "reset_available": False,
        "status": "Network managed by host",
        "interfaces": [],
    }
    if Path(HELPER).is_file():
        try:
            response = run(HELPER, "inspect")
            if response.returncode == 0:
                data = json.loads(response.stdout)
                if isinstance(data, dict) and isinstance(data.get("interfaces"), list):
                    result.update(data)
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    wireless = any((p / "wireless").is_dir() for p in Path("/sys/class/net").iterdir())
    try:
        iwd = run("systemctl", "is-active", "--quiet", "iwd").returncode == 0
    except (OSError, subprocess.SubprocessError):
        iwd = False
    result["wifi_available"] = wireless and iwd and shutil.which("iwgtk") is not None
    result["wifi_status"] = (
        "Choose a Wi-Fi network"
        if result["wifi_available"]
        else "Wi-Fi managed by host or unavailable"
    )
    return result


def notify(message):
    try:
        run("notify-send", "--app-name", "network", "Network", message)
    except (OSError, subprocess.SubprocessError):
        pass


def start_agent():
    # Existing agents refuse duplicate registration; launch only when this agent
    # is absent. Never elevate the GUI or retain administrator credentials.
    if Path(AGENT).is_file():
        existing = run("pgrep", "-u", str(os.getuid()), "-f", "^" + AGENT + "$")
        if existing.returncode != 0:
            subprocess.Popen(
                [AGENT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(0.4)


def action(command, index):
    current = state()
    if command == "wifi":
        if current["wifi_available"]:
            subprocess.Popen(
                ["iwgtk"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:
            notify(current["wifi_status"])
        return
    if not current["reset_available" if command == "reset" else "available"]:
        notify(current["status"])
        return
    args = [HELPER, "reset"]
    if command == "prefer":
        matches = [
            x
            for x in current["interfaces"]
            if x.get("index") == index and x.get("eligible") and x.get("connected")
        ]
        if len(matches) != 1:
            notify("Connect this interface before preferring it")
            return
        args = [HELPER, "prefer", matches[0]["name"]]
    start_agent()
    response = run("pkexec", "--disable-internal-agent", *args, timeout=180)
    if response.returncode == 0:
        notify("Network preference updated")
    elif response.returncode not in (126, 127):
        notify(response.stderr.strip() or "Network preference could not be updated")
    else:
        notify("Network preference unchanged: authentication cancelled or unavailable")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["state", "wifi", "prefer", "reset"])
    parser.add_argument("index", nargs="?", type=int)
    args = parser.parse_args()
    if args.command == "state":
        print(json.dumps(state()))
    else:
        try:
            action(args.command, args.index)
        except (OSError, ValueError, subprocess.SubprocessError):
            notify("Network action unavailable")


if __name__ == "__main__":
    main()
