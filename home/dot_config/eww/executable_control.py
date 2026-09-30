#!/usr/bin/env python3
"""Small, shell-free desktop controls and JSON state for the Eww panel."""

import argparse
import datetime
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

CONFIG = Path.home() / ".config/eww"


def run(*args: str, timeout: float = 2) -> str | None:
    """Treat absent programs, unavailable services and timeouts as unavailable."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def eww(*args: str) -> str | None:
    return run(
        "eww", "--config", str(CONFIG), *args, timeout=10 if args[0] == "open" else 2
    )


def volume_state() -> dict[str, Any]:
    raw = run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@") or ""
    match = re.search(r"Volume:\s+([0-9.]+)", raw)
    return {
        "available": bool(match),
        "value": round(float(match[1]) * 100) if match else 0,
        "muted": "[MUTED]" in raw,
    }


def state() -> dict[str, Any]:
    now = datetime.datetime.now(datetime.UTC).astimezone()
    status = run("playerctl", "status")
    paused = run("dunstctl", "is-paused")
    return {
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%A, %d %B"),
        "volume": volume_state(),
        "music": {
            "available": status is not None,
            "playing": status == "Playing",
            "title": (run("playerctl", "metadata", "xesam:title") or "Untitled track")
            if status is not None
            else "Nothing playing",
            "artist": (run("playerctl", "metadata", "xesam:artist") or "Media player")
            if status is not None
            else "Start music in a compatible app",
        },
        "notifications": {"available": paused is not None, "paused": paused == "true"},
        "brightness": "Use your monitor's brightness controls",
    }


def refresh() -> None:
    # Avoid state queries when closed, and never start Eww for media-key use.
    active = eww("active-windows") or ""
    if any(line.startswith("control-center:") for line in active.splitlines()):
        eww("update", "desktop=" + json.dumps(state(), ensure_ascii=True))


def notify(
    title: str, body: str, value: int | None = None, tag: str = "volume"
) -> None:
    args = [
        "notify-send",
        "--app-name",
        tag,
        "--expire-time",
        "1500",
        "--hint",
        f"string:x-dunst-stack-tag:{tag}",
    ]
    if value is not None:
        args += ["--hint", f"int:value:{min(100, max(0, value))}"]
    run(*args, title, body)


def volume(action: str, value: float | None = None) -> None:
    if action == "mute":
        result = run("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")
    else:
        target = {"up": "5%+", "down": "5%-"}.get(action, "")
        if action == "set":
            if value is None or not math.isfinite(value):
                raise ValueError("volume set requires a finite number")
            target = f"{min(100, max(0, round(value)))}%"
        result = run(
            "wpctl", "set-volume", "--limit", "1.0", "@DEFAULT_AUDIO_SINK@", target
        )
    current = volume_state()
    if result is None or not current["available"]:
        notify("Audio unavailable", "No default audio output is available")
    else:
        label = "Muted" if current["muted"] else f"{current['value']}%"
        notify("Volume", label, 0 if current["muted"] else current["value"])
    refresh()


def close() -> None:
    eww("update", "panel_open=false")
    eww("close", "control-center")


def toggle() -> None:
    active = eww("active-windows") or ""
    if any(line.startswith("control-center:") for line in active.splitlines()):
        close()
        return
    # Open on the currently focused i3 output, with Eww's primary fallback.
    try:
        workspaces = json.loads(run("i3-msg", "-t", "get_workspaces") or "[]")
        output = next((w["output"] for w in workspaces if w.get("focused")), None)
    except (ValueError, KeyError, TypeError):
        output = None
    args = ["open", "control-center"]
    if output:
        args += ["--screen", output]
    # Daemon children inherit pipes: never capture output during daemon startup.
    try:
        subprocess.run(
            ["eww", "--config", str(CONFIG), "daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    if eww(*args) is not None:
        eww("update", "panel_open=true")
        refresh()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("state", "toggle", "close"):
        commands.add_parser(name)
    audio = commands.add_parser("volume")
    audio.add_argument("action", choices=("up", "down", "mute", "set"))
    audio.add_argument("value", nargs="?", type=float)
    music = commands.add_parser("music")
    music.add_argument("action", choices=("previous", "play-pause", "next"))
    notifications = commands.add_parser("notifications")
    notifications.add_argument("action", choices=("pause", "history"))
    brightness = commands.add_parser("brightness")
    brightness.add_argument("action", choices=("up", "down"))
    args = parser.parse_args()
    if args.command == "state":
        print(json.dumps(state(), ensure_ascii=True))
    elif args.command == "toggle":
        toggle()
    elif args.command == "close":
        close()
    elif args.command == "volume":
        try:
            volume(args.action, args.value)
        except ValueError as error:
            parser.error(str(error))
    elif args.command == "music":
        run("playerctl", args.action)
        refresh()
    elif args.command == "notifications":
        if args.action == "pause":
            run("dunstctl", "set-paused", "toggle")
        else:
            run("dunstctl", "history-pop")
        refresh()
    elif args.command == "brightness":
        notify(
            "Display brightness",
            "Use your monitor's brightness controls",
            tag="brightness",
        )


if __name__ == "__main__":
    main()
