"""Supervise one full-shell theme picker and report completion/failure.

The existing client retains its own identity, selection, timeout and cleanup gates.
No alternate backend, host startup, theme reset or global picker cancellation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

CLIENT = Path("/home/ll931217/.local/share/omarchy-inspired/full-desktop/client.py")
FINISHED = "Picker finished: a selection was applied or the request was cancelled."
FAILED = "Theme request failed or expired. Check the current native shell, then reopen the picker. No fallback or theme reset was attempted."


def load_client():
    spec = importlib.util.spec_from_file_location("_supervised_theme_client", CLIENT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Theme client unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notify(message: str, runner=subprocess.run) -> bool:
    """Address the existing unique notification owner; never activate a daemon."""
    try:
        owner = runner(
            [
                "/usr/bin/busctl",
                "--user",
                "--json=short",
                "--timeout=2",
                "call",
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                "GetNameOwner",
                "s",
                "org.freedesktop.Notifications",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if owner.returncode:
            return False
        data = json.loads(owner.stdout)
        if not isinstance(data, dict):
            return False
        values = data.get("data")
        if (
            data.get("type") != "s"
            or not isinstance(values, list)
            or len(values) != 1
            or not isinstance(values[0], str)
            or not re.fullmatch(r":[0-9]+\.[0-9]+", values[0])
        ):
            return False
        result = runner(
            [
                "/usr/bin/busctl",
                "--user",
                "--auto-start=no",
                "--timeout=2",
                "call",
                values[0],
                "/org/freedesktop/Notifications",
                "org.freedesktop.Notifications",
                "Notify",
                "susssasa{sv}i",
                "Omarchy themes",
                "0",
                "",
                "Theme picker",
                message,
                "0",
                "0",
                "6000",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return result.returncode == 0
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return False


def request(client=None, notifier: Callable[[str], bool] = notify) -> int:
    try:
        code = (client or load_client()).main(["--themes"])
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ):
        code = 1
    message = FINISHED if code == 0 else FAILED
    print(message, file=sys.stdout if code == 0 else sys.stderr, flush=True)
    if not notifier(message):
        print(
            "Theme result notification unavailable; result recorded in the session log.",
            file=sys.stderr,
            flush=True,
        )
    return 0 if code == 0 else 1


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__, allow_abbrev=False).parse_args(argv)
    return request()


if __name__ == "__main__":
    raise SystemExit(main())
