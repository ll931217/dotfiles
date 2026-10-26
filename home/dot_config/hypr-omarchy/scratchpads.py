"""Named special-workspace scratchpads using the Hyprland 0.56 native Lua IPC API."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from desktop_actions import HOME, ActionError, address, executable

CLASSES = {
    "terminal": "special-scratchpad",
    "droid": "ai-scratchpad",
    "purple": "purple-scratchpad",
    "spotify": "spotify",
    "chatgpt": "chatgpt",
}


def matches(client, kind):
    expected = CLASSES[kind]
    return any(
        str(client.get(key, "")).lower() == expected
        for key in ("class", "initialClass")
    )


def command(kind):
    if kind in ("terminal", "droid", "purple"):
        terminal = "/usr/local/bin/st"
        executable(terminal)
        args = [terminal, "-c", CLASSES[kind], "-n", CLASSES[kind]]
        if kind != "terminal":
            payload = HOME / ".local/bin" / kind
            executable(str(payload))
            args += ["-e", str(payload)]
        return args
    if kind == "spotify":
        return [executable("spotify")]
    # Installed desktop metadata uses Exec=chatgpt %U; its launcher resolves ChatGPT.
    desktop = Path("/usr/share/applications/chatgpt.desktop")
    if not desktop.is_file() or "Exec=chatgpt %U" not in desktop.read_text():
        raise ActionError(
            "ChatGPT desktop metadata is missing/unrecognized; restore the desktop package before retrying. No web/provider request was made."
        )
    return [executable("chatgpt")]


def geometry(monitor, fraction):
    scale = float(monitor.get("scale", 1))
    if scale <= 0:
        raise ActionError(
            "Invalid monitor scale; correct the Hyprland monitor configuration and retry."
        )
    width, height = int(monitor["width"]), int(monitor["height"])
    if int(monitor.get("transform", 0)) % 2:
        width, height = height, width
    width, height = int(width / scale), int(height / scale)
    left, top, right, bottom = monitor.get("reserved", [0, 0, 0, 0])
    usable_width, usable_height = width - left - right, height - top - bottom
    size_x, size_y = int(usable_width * fraction), int(usable_height * fraction)
    return (
        size_x,
        size_y,
        int(monitor["x"] + left + (usable_width - size_x) / 2),
        int(monitor["y"] + top + (usable_height - size_y) / 2),
    )


def show(session, kind, client, *, force=False):
    target = address(client["address"])
    workspace = "omarchy-" + kind
    monitors = session.query("monitors")
    monitor = next((m for m in monitors if m.get("focused")), None)
    if monitor is None:
        raise ActionError(
            "No focused Hyprland monitor; focus a physical display and retry the scratchpad."
        )
    special = monitor.get("specialWorkspace", {}).get("name", "")
    active = session.query("activewindow")
    visible_here = special == "special:" + workspace
    if visible_here and active.get("address") == target and not force:
        session.dispatch(f'hl.dsp.workspace.toggle_special("{workspace}")')
        print(f"Scratchpad {kind}: hidden; app kept running.")
        return
    if client.get("workspace", {}).get("name") != "special:" + workspace:
        session.dispatch(
            f'hl.dsp.window.move({{workspace="special:{workspace}",follow=false,window="address:{target}"}})'
        )
    if not visible_here:
        session.dispatch(f'hl.dsp.workspace.toggle_special("{workspace}")')
    if client.get("fullscreen", 0) or client.get("fullscreenClient", 0):
        session.dispatch(
            f'hl.dsp.window.fullscreen_state({{internal=0,client=0,action="set",window="address:{target}"}})'
        )
    # 0.56.2 parseToggleStr: on/enable is idempotent; unknown "set" toggles.
    # Enforce floating after workspace placement, before pixel geometry.
    session.dispatch(f'hl.dsp.window.float({{action="on",window="address:{target}"}})')
    size_x, size_y, x, y = geometry(monitor, 0.90 if kind == "chatgpt" else 0.80)
    session.dispatch(
        f'hl.dsp.window.resize({{x={size_x},y={size_y},relative=false,window="address:{target}"}})'
    )
    session.dispatch(
        f'hl.dsp.window.move({{x={x},y={y},relative=false,window="address:{target}"}})'
    )
    session.dispatch(f'hl.dsp.focus({{window="address:{target}"}})')
    print(
        f"Scratchpad {kind}: shown centered on {monitor['name']}; existing app reused. "
        + ("st uses XWayland." if kind in ("terminal", "droid", "purple") else "")
    )


def cycle(session):
    clients = session.query("clients")
    available = [
        (kind, client)
        for kind in CLASSES
        for client in clients
        if matches(client, kind)
    ]
    if not available:
        session.notify(
            "Scratchpads",
            "None open; Super+A/C/X/S or Super+grave opens one. Cycling never spawns an app.",
        )
        return
    active = session.query("activewindow").get("address")
    current = next(
        (i for i, (_, client) in enumerate(available) if client["address"] == active),
        -1,
    )
    kind, client = available[(current + 1) % len(available)]
    show(session, kind, client, force=True)


def toggle(session, kind):
    if kind == "cycle":
        with session.locked("scratchpads"):
            cycle(session)
        return
    if kind not in CLASSES:
        raise ActionError(
            "Unknown scratchpad; choose scratch-terminal/droid/purple/spotify/chatgpt/cycle from --list."
        )
    with session.locked("scratchpads"):
        pending = session.runtime() / ("scratch-" + kind + ".json")
        clients = [c for c in session.query("clients") if matches(c, kind)]
        if clients:
            pending.unlink(missing_ok=True)
            show(session, kind, clients[0])
            return
        if pending.exists():
            raise ActionError(
                f"{kind} launch is pending; no duplicate started. Check the app/XWayland. Only after closing any failed instance, remove {pending} to permit another launch."
            )
        args = command(kind)
        session.save(pending, {"kind": kind, "pending": True})
        try:
            subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            pending.unlink(missing_ok=True)
            raise
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            clients = [c for c in session.query("clients") if matches(c, kind)]
            if clients:
                pending.unlink(missing_ok=True)
                show(session, kind, clients[0], force=True)
                return
            time.sleep(0.15)
        raise ActionError(
            f"{kind} launched but no window appeared within 10 seconds; check app/XWayland, then retry to reuse it. Duplicate spawning is blocked by {pending}."
        )
