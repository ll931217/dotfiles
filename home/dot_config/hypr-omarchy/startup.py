"""Ordered profile startup; --check is read-only and never starts helpers.

Existing services/processes are never restarted, adopted, or stopped. New tray
and launcher processes are direct children, stopped when this compositor ends.
The existing helper and full-shell supervisors retain their own cleanup policy.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import os
import signal
import stat
import subprocess
import sys
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

HOME = Path("/home/ll931217")
SESSION = HOME / ".local/share/omarchy-inspired/full-desktop/session.py"
WRAPPER = HOME / ".local/bin/omarchy-inspired-session"
ENVIRONMENT = (
    "DISPLAY",
    "XAUTHORITY",
    "WAYLAND_DISPLAY",
    "HYPRLAND_INSTANCE_SIGNATURE",
    "XDG_RUNTIME_DIR",
    "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP",
    "XDG_SESSION_TYPE",
    "XCURSOR_SIZE",
    "HYPRCURSOR_SIZE",
    "GTK_IM_MODULE",
    "QT_IM_MODULE",
    "XMODIFIERS",
    "GDK_BACKEND",
    "QT_QPA_PLATFORM",
    "MOZ_ENABLE_WAYLAND",
    "ELECTRON_OZONE_PLATFORM_HINT",
    "OZONE_PLATFORM",
)
HELPERS = (
    ("xembedsniproxy", (str(HOME / ".local/bin/xembedsniproxy"),), "DISPLAY"),
    ("vicinae", ("/usr/bin/vicinae", "server"), "WAYLAND_DISPLAY"),
)
EXECUTABLES = {
    "xembedsniproxy": HOME / ".local/bin/xembedsniproxy",
    "vicinae": Path("/usr/libexec/vicinae/vicinae-server"),
}


class Child(Protocol):
    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...


def load_session():
    spec = importlib.util.spec_from_file_location("_profile_startup_session", SESSION)
    if spec is None or spec.loader is None:
        raise RuntimeError("Session verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(argv, env):
    return subprocess.run(
        argv, env=env, capture_output=True, text=True, timeout=10, check=False
    )


def helper_state(name, display_key, env, session, runner=run):
    """Return a plan without inspecting settings, titles, clipboard or credentials."""
    result = runner(
        [
            "/usr/bin/systemctl",
            "--user",
            "show",
            name + ".service",
            "--property=LoadState,ActiveState,MainPID",
        ],
        env,
    )
    fields = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    if (
        result.returncode not in (0, 1)
        or (result.returncode == 1 and fields.get("LoadState") != "not-found")
        or not {"ActiveState", "MainPID"}.issubset(fields)
    ):
        raise RuntimeError("Cannot establish helper service state")
    active = fields.get("ActiveState")
    pid = int(fields.get("MainPID", "0"))
    if active == "active" and pid > 1:
        process = session.handoff.identity(pid)
        expected = str(EXECUTABLES[name])
        if process.uid != os.getuid() or process.exe != expected:
            raise RuntimeError("Unexpected existing helper identity")
        inherited = session.proc_environment(pid)
        keys = [display_key, "XDG_RUNTIME_DIR"]
        if name == "xembedsniproxy" and env.get("XAUTHORITY"):
            keys.append("XAUTHORITY")  # Path metadata only; never read the cookie.
        same = all(inherited.get(key) == env.get(key) for key in keys)
        session.handoff.unchanged(process)
        return "reuse" if same else "stale"
    if active not in ("inactive", "failed") or pid != 0:
        return "busy"
    # Also preserve instances started outside systemd. Never use --replace.
    result = subprocess.run(
        ["/usr/bin/pgrep", "-u", str(os.getuid()), "-x", EXECUTABLES[name].name],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Cannot establish existing helper presence")
    return "external" if result.returncode == 0 else "start"


@contextmanager
def startup_lock(current, session):
    path = current.directory / (
        "omarchy-inspired-startup-" + current.signature + ".lock"
    )
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if (
            info.st_uid != os.getuid()
            or not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
        ):
            raise RuntimeError("Unsafe startup lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if session.desktop(dict(os.environ)) != current:
            raise RuntimeError("Compositor changed before startup")
        yield
    finally:
        os.close(fd)


def stop_children(children):
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
    for child in reversed(children):
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


def start(
    env, session, current, runner=run, spawn: Callable[..., Child] = subprocess.Popen
):
    names = [name for name in ENVIRONMENT if env.get(name)]
    if not all(env.get(name) for name in ("DISPLAY", "WAYLAND_DISPLAY")):
        raise RuntimeError("Both graphical display variables are required")
    # One explicit allowlist updates both managers, before any dependent process.
    if runner(
        ["/usr/bin/dbus-update-activation-environment", "--systemd", *names], env
    ).returncode:
        raise RuntimeError("Activation environment import failed")
    if session.desktop(env) != current:
        raise RuntimeError("Compositor changed during environment setup")
    children = []
    try:
        monitor = spawn(
            [
                "/usr/bin/socat",
                "-u",
                f"UNIX-CONNECT:{current.directory}/hypr/{current.signature}/.socket2.sock",
                "/dev/null",
            ],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            close_fds=True,
        )
        children.append(monitor)
        for name, argv, display in HELPERS:
            state = helper_state(name, display, env, session, runner)
            print(
                f"Startup {name}: {state}; pre-existing processes are left unchanged.",
                flush=True,
            )
            if state == "start":
                if monitor.poll() is not None or session.desktop(env) != current:
                    raise RuntimeError("Compositor ended before helper startup")
                helper_env = (
                    {**env, "QT_QPA_PLATFORM": "xcb"}
                    if name == "xembedsniproxy"
                    else env
                )
                children.append(
                    spawn(
                        list(argv),
                        env=helper_env,
                        stdin=subprocess.DEVNULL,
                        close_fds=True,
                    )
                )
            elif state in ("stale", "busy", "external"):
                print(
                    f"Startup {name}: not rebound or adopted. Review the existing instance before a fresh login; do not run startup.py to restart it.",
                    file=sys.stderr,
                    flush=True,
                )
        # These supervisors already verify their profile and own their lifetimes.
        supervisors = []
        for argv in (
            [str(WRAPPER), "--services"],
            [str(WRAPPER), "--handy"],
            ["/usr/bin/python", "-I", "-B", str(SESSION)],
        ):
            if monitor.poll() is not None or session.desktop(env) != current:
                raise RuntimeError("Compositor ended before supervisor startup")
            supervisors.append(
                spawn(
                    argv,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    close_fds=True,
                    start_new_session=True,
                )
            )
        return monitor.wait()
    finally:
        # Never signal systemd services, reused instances or the full-shell root.
        stop_children(children)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read-only profile and helper plan; no environment writes or launches",
    )
    args = parser.parse_args(argv)
    try:
        env = dict(os.environ)
        session = load_session()
        current = session.desktop(env)
        if args.check:
            for name, _, display in HELPERS:
                print(f"{name}: {helper_state(name, display, env, session)}")
            print("Startup profile verified; check only, no changes made.")
            return 0
        with startup_lock(current, session):
            return start(env, session, current)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print(
            "Startup refused: profile, environment, helper or ownership check failed. Check the session log; existing services were not restarted.",
            file=sys.stderr,
        )
        return 2


def interrupted(_signum, _frame):
    raise SystemExit(0)


if __name__ == "__main__":
    for number in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        signal.signal(number, interrupted)
    raise SystemExit(main())
