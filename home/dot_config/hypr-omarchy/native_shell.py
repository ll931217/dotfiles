"""Per-action native shell routing. Status probes never start or refresh a host."""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

import desktop_actions as actions

FULL_CLIENT = actions.HOME / ".local/share/omarchy-inspired/full-desktop/client.py"
LEGACY_CLIENT = actions.NATIVE_LAUNCHER
RUNTIME_BASE = actions.HOME / ".local/state/omarchy-inspired"


def command(client: Path, flag: str) -> list:
    return ["/usr/bin/python", "-I", client, flag]


def status(session, client: Path) -> dict | None:
    try:
        result = session.run(command(client, "--status"), check=False)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return data if isinstance(data, dict) and data.get("running") is True else None
    except (actions.ActionError, ValueError, TypeError, OSError):
        return None


def full_root(value) -> Path:
    """Trust the fixed client's identity proof, not arbitrary returned paths."""
    if not isinstance(value, str):
        raise actions.ActionError(
            "Full native: missing runtime root; no fallback attempted."
        )
    root = Path(value)
    if (
        not root.is_absolute()
        or str(root) != value
        or root.parent != RUNTIME_BASE
        or not re.fullmatch(r"full-desktop-runtime-v[0-9]+", root.name)
    ):
        raise actions.ActionError(
            "Full native: refused runtime root; no fallback attempted."
        )
    try:
        helper = root / "bin/omarchy-shell"
        if any(p.is_symlink() for p in (helper, *helper.parents)):
            raise ValueError("symlink")
        for path in (root, helper.parent, helper):
            info = path.stat()
            expected = stat.S_ISREG if path == helper else stat.S_ISDIR
            if (
                not expected(info.st_mode)
                or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o700
            ):
                raise ValueError("ownership/type/mode")
    except (OSError, ValueError) as exc:
        raise actions.ActionError(
            "Full native: unsafe runtime/helper ownership or permissions; no fallback attempted."
        ) from exc
    return root


@dataclass(frozen=True)
class Backend:
    client: Path
    root: Path | None = None


def select(session) -> Backend:
    full = status(session, FULL_CLIENT)
    if full is not None:
        return Backend(FULL_CLIENT, full_root(full.get("root")))
    if status(session, LEGACY_CLIENT) is not None:
        return Backend(LEGACY_CLIENT)
    raise actions.ActionError(
        "Native shell unavailable: neither full nor legacy status verified a running host. "
        "Check the current login's shell service; no host or Dunst was started."
    )


def panel(session, name: str, label: str) -> None:
    backend = select(session)
    try:
        actions.launch(session, command(backend.client, "--" + name), label)
    except (actions.ActionError, OSError) as exc:
        kind = "Full" if backend.root is not None else "Legacy"
        raise actions.ActionError(
            f"{kind} native: {exc}; no fallback attempted."
        ) from exc
    print(f"Native panel backend: {'full' if backend.root is not None else 'legacy'}.")


def dunst_owner(session) -> str | None:
    """Ask only the bus daemon: never activate a notification service."""
    owners = []
    try:
        for name in ("org.knopwob.dunst", "org.freedesktop.Notifications"):
            reply = session.run(
                [
                    "/usr/bin/busctl",
                    "--user",
                    "--json=short",
                    "--no-pager",
                    "call",
                    "org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus",
                    "GetNameOwner",
                    "s",
                    name,
                ],
                check=False,
            )
            if reply.returncode:
                return None
            data = json.loads(reply.stdout)
            if not isinstance(data, dict):
                return None
            owner = data.get("data")
            if (
                data.get("type") != "s"
                or not isinstance(owner, list)
                or len(owner) != 1
                or not isinstance(owner[0], str)
                or not re.fullmatch(r":[0-9]+\.[0-9]+", owner[0])
            ):
                return None
            owners.append(owner[0])
    except (actions.ActionError, ValueError, TypeError, OSError):
        return None
    return owners[0] if owners[0] == owners[1] else None


def notifications(session, name: str) -> None:
    backend = select(session)
    if backend.root is not None:
        operation = "openPanel" if name == "notification-history" else "toggleDnd"
        try:
            session.run(
                [backend.root / "bin/omarchy-shell", "notifications", operation]
            )
        except actions.ActionError as exc:
            raise actions.ActionError(
                f"Full native notifications: {exc}; no fallback attempted."
            ) from exc
        print(f"Full native notifications: {operation} requested.")
        return
    if dunst_owner(session) is None:
        raise actions.ActionError(
            "Legacy native: Dunst is not the current notification owner; no action sent."
        )
    actions.executable("dunstctl")
    if name == "notification-history":
        session.run(["dunstctl", "history-pop"])
        print(
            "Legacy Dunst: requested latest history notification; empty history displays nothing."
        )
    else:
        session.run(["dunstctl", "set-paused", "toggle"])
        paused = session.run(["dunstctl", "is-paused"]).stdout.strip()
        if paused not in ("true", "false"):
            raise actions.ActionError(
                "Legacy Dunst pause status unreadable; run dunstctl is-paused to check it."
            )
        session.notify(
            "Notifications",
            "Paused; Super+Ctrl+N resumes."
            if paused == "true"
            else "Resumed; Super+N opens history.",
        )
