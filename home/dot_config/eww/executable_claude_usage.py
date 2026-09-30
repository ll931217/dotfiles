#!/usr/bin/env python3
"""Capture documented Claude status-line quotas, preserving the original renderer."""

import fcntl
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

usage = importlib.import_module(
    "executable_usage" if Path(__file__).name.startswith("executable_") else "usage"
)
CACHE, load, save, window = usage.CACHE, usage.load, usage.save, usage.window


STATE = (
    Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "eww-usage"
)


def capture(raw):
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return
    limits = data.get("rate_limits") if isinstance(data, dict) else None
    if not isinstance(limits, dict):
        return
    windows = []
    for name, label in (
        ("five_hour", "5h"),
        ("seven_day", "7d"),
        ("spend_limit", "Spend limit"),
    ):
        quota = limits.get(name)
        if isinstance(quota, dict):
            item = window(label, quota.get("used_percentage"), quota.get("resets_at"))
            if item:
                windows.append(item)
    save(CACHE / "claude.json", {"windows": windows, "updated_at": time.time()})


def install(uninstall=False):
    settings = Path.home() / ".claude/settings.json"
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    command = f'python3 "{Path.home()}/.config/eww/claude_usage.py"'
    with (STATE / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        original = settings.read_text() if settings.exists() else "{}"
        data = json.loads(original)
        old = data.get("statusLine")
        if uninstall:
            if not isinstance(old, dict) or old.get("command") != command:
                return
            saved = load(STATE / "original-statusline.json")
            if "statusLine" not in saved:
                raise ValueError(
                    "Original status line missing; settings left unchanged"
                )
            if saved["statusLine"] is None:
                data.pop("statusLine")
            else:
                data["statusLine"] = saved["statusLine"]
            if settings.read_text() != original:
                raise ValueError("Settings changed concurrently; retry removal")
            save(settings, data)
            (STATE / "original-statusline.json").unlink()
            return
        if isinstance(old, dict) and old.get("command") == command:
            return
        if old is not None and (
            not isinstance(old, dict)
            or old.get("type") != "command"
            or not isinstance(old.get("command"), str)
        ):
            raise ValueError("Unsupported existing status line; left unchanged")
        save(STATE / "original-statusline.json", {"statusLine": old})
        if (settings.read_text() if settings.exists() else "{}") != original:
            raise ValueError("Settings changed concurrently; retry installation")
        data["statusLine"] = {**(old or {}), "type": "command", "command": command}
        save(settings, data)


def main():
    if "--uninstall" in sys.argv:
        install(uninstall=True)
        return 0
    if "--install" in sys.argv:
        install()
        return 0
    raw = sys.stdin.buffer.read()
    try:
        capture(raw)
    except (OSError, ValueError):
        pass
    old = load(STATE / "original-statusline.json").get("statusLine")
    if isinstance(old, dict) and isinstance(old.get("command"), str):
        # This is the user's existing trusted command, not model or network input.
        return subprocess.run(
            ["bash", "-c", old["command"]], input=raw, check=False
        ).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
