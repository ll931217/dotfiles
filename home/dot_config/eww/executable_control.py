#!/usr/bin/env python3
"""Small, shell-free desktop controls and JSON state for the Eww panel."""

import argparse
import datetime
import json
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

CONFIG = Path.home() / ".config/eww"


def run(*args: str, timeout: float = 2, c_locale: bool = False) -> str | None:
    """Treat absent programs, unavailable services and timeouts as unavailable."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "LC_ALL": "C"} if c_locale else None,
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
    match = re.search(r"Volume:\s+([0-9]+(?:\.[0-9]+)?)", raw)
    if match:
        return {
            "available": True,
            "backend": "wpctl",
            "value": round(float(match[1]) * 100),
            "muted": "[MUTED]" in raw,
        }
    raw = run("pactl", "get-sink-volume", "@DEFAULT_SINK@", c_locale=True) or ""
    levels = [int(value) for value in re.findall(r"(\d+)%", raw)]
    mute = run("pactl", "get-sink-mute", "@DEFAULT_SINK@", c_locale=True)
    available = bool(levels) and mute in ("Mute: yes", "Mute: no")
    return {
        "available": available,
        "backend": "pactl" if available else "",
        "value": max(levels) if available else 0,
        "muted": mute == "Mute: yes",
    }


def state(full: bool = True) -> dict[str, Any]:
    now = datetime.datetime.now(datetime.UTC).astimezone()
    status = run("playerctl", "status") if full else None
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
    if any(line.startswith("bar-") for line in active.splitlines()):
        eww("update", "bar_status=" + json.dumps(state(full=False), ensure_ascii=True))
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
    if action not in ("up", "down", "mute", "set"):
        raise ValueError("unknown volume action")
    if action == "set" and (value is None or not math.isfinite(value)):
        raise ValueError("volume set requires a finite number")
    before = volume_state()
    result = None
    if before["backend"] == "wpctl":
        if action == "mute":
            result = run("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle")
        else:
            target = {"up": "5%+", "down": "5%-"}.get(action)
            if target is None:
                target = f"{min(100, max(0, round(value or 0)))}%"
            result = run(
                "wpctl", "set-volume", "--limit", "1.0", "@DEFAULT_AUDIO_SINK@", target
            )
    elif before["backend"] == "pactl":
        if action == "mute":
            result = run("pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle")
        else:
            target_value = (
                value
                if action == "set"
                else before["value"] + (5 if action == "up" else -5)
            )
            bounded = min(100, max(0, round(target_value or 0)))
            # Relative adjustments preserve unequal channel levels on VDI sinks.
            target = (
                f"{bounded}%" if action == "set" else f"{bounded - before['value']:+d}%"
            )
            result = run("pactl", "set-sink-volume", "@DEFAULT_SINK@", target)
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


def toggle(monitor_index: int | None = None) -> None:
    active = eww("active-windows") or ""
    try:
        workspaces = json.loads(run("i3-msg", "-t", "get_workspaces") or "[]")
        focused = next((w["output"] for w in workspaces if w.get("focused")), None)
        outputs = [
            o
            for o in json.loads(run("i3-msg", "-t", "get_outputs") or "[]")
            if o.get("active")
        ]
        if monitor_index is not None:
            if not 0 <= monitor_index < len(outputs):
                return
            monitor = outputs[monitor_index]
        else:
            monitor = next((o for o in outputs if o["name"] == focused), None)
            if monitor is None:
                monitor = next(
                    (o for o in outputs if o.get("primary")),
                    outputs[0] if outputs else None,
                )
    except (ValueError, KeyError, TypeError):
        return
    if monitor is None:
        return
    output = monitor["name"]
    if any(line.startswith("control-center:") for line in active.splitlines()):
        same_output = eww("get", "panel_output") == output
        close()
        if same_output:
            return
    width = min(400, max(240, int(monitor["rect"]["width"]) - 32))
    height = min(840, max(220, int(monitor["rect"]["height"]) - 96))
    args = [
        "open",
        "control-center",
        "--size",
        f"{width}x{height}",
        "--arg",
        "target=" + output,
    ]
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
        eww("update", "panel_open=true", "panel_output=" + output)
        refresh()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("state", "bar-state", "close"):
        commands.add_parser(name)
    panel = commands.add_parser("toggle")
    panel.add_argument("--monitor", type=int)
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
    if args.command in ("state", "bar-state"):
        print(json.dumps(state(full=args.command == "state"), ensure_ascii=True))
    elif args.command == "toggle":
        toggle(args.monitor)
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
