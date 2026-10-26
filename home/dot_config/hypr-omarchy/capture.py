"""Wayland capture/editor and session-owned system-audio recorder lifecycle."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from desktop_actions import HOME, ActionError, executable


def primary_output(monitors):
    enabled = [
        m
        for m in monitors
        if not m.get("disabled", False) and m.get("mirrorOf") in (None, "", "none")
    ]
    if not enabled:
        raise ActionError(
            "No active recording output; enable a physical Hyprland display and retry."
        )
    selected = next((m for m in enabled if m.get("primary")), None)
    selected = selected or next(
        (m for m in enabled if m.get("x") == 0 and m.get("y") == 0), None
    )
    selected = selected or next((m for m in enabled if m.get("focused")), enabled[0])
    name = selected["name"]
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", name):
        raise ActionError(
            "Invalid Hyprland output name; check display configuration and retry recording."
        )
    return name


def monitor_source(session):
    executable("pactl")
    sink = session.run(["pactl", "get-default-sink"]).stdout.strip()
    if not sink or "\n" in sink:
        raise ActionError(
            "No default system-audio sink; select an output in Super+B → Audio and retry recording."
        )
    sources = json.loads(session.run(["pactl", "-f", "json", "list", "sources"]).stdout)
    name = sink + ".monitor"
    if not any(source.get("name") == name for source in sources):
        raise ActionError(
            "Default output has no verified .monitor audio source; configure a PulseAudio/PipeWire output monitor and retry. Microphone fallback is forbidden."
        )
    return name


def process_identity(pid):
    proc = Path("/proc") / str(pid)
    try:
        fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
        return {
            "pid": pid,
            "start": fields[19],
            "exe": str((proc / "exe").resolve(strict=True)),
            "argv": (proc / "cmdline").read_bytes().rstrip(b"\0").decode().split("\0"),
            "uid": proc.stat().st_uid,
        }
    except OSError, ValueError, IndexError, UnicodeError:
        return None


def same_process(record, actual):
    expected = record.get("identity", {})
    return (
        actual is not None
        and expected.get("uid") == os.getuid()
        and all(
            actual.get(key) == expected.get(key)
            for key in ("pid", "start", "exe", "argv", "uid")
        )
        and Path(expected.get("exe", "")).name == "wf-recorder"
        and expected.get("argv") == record.get("command")
    )


def read_record(path):
    try:
        record = json.loads(path.read_text())
        if not isinstance(record, dict) or not isinstance(
            record.get("identity", {}).get("pid"), int
        ):
            raise TypeError("identity missing")
        return record
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise ActionError(
            f"Recorder state is unreadable; inspect {path} before retrying. No process was signalled."
        ) from exc


def start(session):
    executable("wf-recorder")
    if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
        raise ActionError(
            "Python/Linux pidfd support is required for safe recording; update the runtime before retrying."
        )
    with session.locked("recorder"):
        state = session.runtime() / "recorder.json"
        if state.exists():
            record = read_record(state)
            if same_process(record, process_identity(record["identity"]["pid"])):
                session.notify(
                    "Recording already running",
                    f"Output: {record['output']}; Super+Shift+V stops this recorder only.",
                )
                return
            raise ActionError(
                f"Recorder state is stale or identity changed; inspect {state} and remove it only after confirming the old recorder exited. No duplicate started."
            )
        output_name = primary_output(session.query("monitors"))
        audio = monitor_source(session)
        directory = HOME / "Videos/Hyprland-recordings"
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if directory.is_symlink() or directory.stat().st_uid != os.getuid():
            raise ActionError(
                f"Unsafe recording directory {directory}; restore your own directory before recording."
            )
        filename = directory / (
            datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_")
            + uuid.uuid4().hex[:8]
            + ".mkv"
        )
        command = [
            executable("wf-recorder"),
            "-o",
            output_name,
            "--audio=" + audio,
            "-f",
            str(filename),
        ]
        log = session.runtime() / "recorder.log"
        with log.open("wb") as stream:
            child = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=stream,
                start_new_session=True,
                umask=0o077,
            )
        identity = process_identity(child.pid)
        if identity is None:
            child.wait(timeout=5)
            raise ActionError(
                f"Recorder exited before ownership could be recorded; inspect {log}, then retry."
            )
        record = {
            "identity": identity,
            "command": command,
            "output": str(filename),
            "monitor": output_name,
        }
        try:
            session.save(state, record)
        except OSError:
            child.send_signal(signal.SIGINT)
            child.wait(timeout=5)
            raise
        time.sleep(0.25)
        if child.poll() is not None:
            state.unlink(missing_ok=True)
            raise ActionError(
                f"wf-recorder could not start; inspect {log} for capture/audio permissions and retry. Partial output may be at {filename}."
            )
        session.notify(
            "Recording started",
            f"{output_name} + system audio only (no microphone) → {filename}. Super+Shift+V stops this owned recording.",
        )


def stop(session):
    with session.locked("recorder"):
        state = session.runtime() / "recorder.json"
        if not state.exists():
            session.notify(
                "Recording already stopped",
                "No recorder owned by this session; other recorders are untouched.",
            )
            return
        record = read_record(state)
        pid = record["identity"]["pid"]
        if (
            pid <= 1
            or not hasattr(os, "pidfd_open")
            or not hasattr(signal, "pidfd_send_signal")
        ):
            raise ActionError(
                "Safe recorder PID/pidfd support is unavailable; inspect recorder state manually. No process was signalled."
            )
        try:
            fd = os.pidfd_open(pid)
        except ProcessLookupError:
            state.unlink()
            session.notify(
                "Recording already stopped",
                f"Owned recorder exited; inspect saved output at {record['output']}.",
            )
            return
        try:
            if not same_process(record, process_identity(pid)):
                raise ActionError(
                    f"Recorder identity changed; inspect {state} before removing stale state. No process was signalled."
                )
            signal.pidfd_send_signal(fd, signal.SIGINT)
            import select

            readable, _, _ = select.select([fd], [], [], 8)
            if not readable:
                raise ActionError(
                    f"Recorder is still finalizing {record['output']}; wait, then retry stop. No forced kill was used."
                )
            state.unlink()
            session.notify(
                "Recording stopped",
                f"Saved output: {record['output']}. Only this session recorder was stopped.",
            )
        finally:
            os.close(fd)


def screenshot(session):
    for tool in ("slurp", "grim", "satty", "wl-copy"):
        executable(tool)
    selection = session.run(["slurp"], check=False)
    if selection.returncode == 1 and selection.stderr.strip() in (
        "",
        "selection cancelled",
    ):
        session.notify(
            "Screenshot cancelled",
            "No image captured; Super+Shift+S selects another region.",
        )
        return
    if selection.returncode:
        raise ActionError(
            "slurp could not select a region; check the Wayland session and retry Super+Shift+S."
        )
    region = selection.stdout.strip()
    if not re.fullmatch(r"-?\d+,-?\d+ [1-9]\d*x[1-9]\d*", region):
        raise ActionError(
            "slurp returned an invalid region; retry Super+Shift+S and select a rectangle."
        )
    image = session.run(["grim", "-g", region, "-"], input=b"")
    if not image.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ActionError(
            "grim returned no PNG image; check Wayland capture support and retry Super+Shift+S."
        )
    output = str(HOME / "Pictures/Screenshot-%Y-%m-%d_%H-%M-%S.png")
    session.notify(
        "Screenshot ready in Satty",
        "Annotate, press Enter to copy, Save to write ~/Pictures/Screenshot-<date>_<time>.png, or Esc to close. Nothing saves automatically.",
    )
    session.run(
        [
            "satty",
            "--filename",
            "-",
            "--resize",
            "smart",
            "--floating-hack",
            "--app-id",
            "com.omarchy.Screenshot",
            "--title",
            "Screenshot editor",
            "--copy-command",
            "wl-copy",
            "--output-filename",
            output,
            "--actions-on-enter",
            "save-to-clipboard",
            "--actions-on-escape",
            "exit",
        ],
        input=image.stdout,
    )
    print(
        "Satty closed; images are saved only when you choose Save. Default save location: ~/Pictures."
    )


def perform(session, action):
    {"record-start": start, "record-stop": stop, "screenshot-editor": screenshot}[
        action
    ](session)
