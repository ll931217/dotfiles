#!/usr/bin/env python3
"""Manage per-output Eww bars and stream i3 workspace changes without polling."""

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

CONFIG = Path.home() / ".config/eww"


def run(*args: str) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=5, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def query(kind: str) -> list[dict[str, Any]]:
    try:
        result = json.loads(run("i3-msg", "-t", kind) or "[]")
        return result if isinstance(result, list) else []
    except ValueError:
        return []


def eww(*args: str) -> str:
    return run("eww", "--config", str(CONFIG), *args)


def workspaces() -> list[dict[str, Any]]:
    # Use numeric i3 IDs for actions; names are display-only, never shell input.
    return [
        {
            "id": w["id"],
            "name": w["name"],
            "output": w["output"],
            "focused": w["focused"],
            "visible": w["visible"],
            "urgent": w["urgent"],
        }
        for w in query("get_workspaces")
    ]


def sync_bars() -> None:
    outputs = [o for o in query("get_outputs") if o.get("active")]
    if not outputs:
        return
    primary = next((o["name"] for o in outputs if o.get("primary")), outputs[0]["name"])
    active = {line.split(":", 1)[0] for line in eww("active-windows").splitlines()}
    desired = {"bar-" + o["name"] for o in outputs}
    for stale in active - desired:
        if stale.startswith("bar-"):
            eww("close", stale)
    for index, output in enumerate(outputs):
        name = output["name"]
        # Reopening an ID updates monitor geometry and primary tray ownership.
        eww(
            "open",
            "bar",
            "--id",
            "bar-" + name,
            "--screen",
            name,
            "--arg",
            "output=" + name,
            "--arg",
            "primary=" + str(name == primary).lower(),
            "--arg",
            f"monitor_index={index}",
        )


def start() -> None:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    with (runtime / "eww-bars.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
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
        sync_bars()


def stop_listener(_signum: int, _frame: Any) -> None:
    raise SystemExit(0)


def listen() -> None:
    signal.signal(signal.SIGTERM, stop_listener)
    while True:
        print(json.dumps(workspaces(), ensure_ascii=True), flush=True)
        try:
            process = subprocess.Popen(
                ["i3-msg", "-m", "-t", "subscribe", '["workspace","output"]'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except OSError:
            time.sleep(2)
            continue
        try:
            assert process.stdout is not None
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("change") == "unspecified":
                    # Reopening the final bar stops this listener. Reconcile in
                    # a separate session so hotplug completes after that stop.
                    child = subprocess.Popen(
                        [sys.executable, str(CONFIG / "bar.py"), "start"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    threading.Thread(target=child.wait, daemon=True).start()
                print(json.dumps(workspaces(), ensure_ascii=True), flush=True)
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "listen", "workspace"))
    parser.add_argument("workspace_id", type=int, nargs="?")
    args = parser.parse_args()
    if args.action == "start":
        start()
    elif args.action == "listen":
        listen()
    elif args.workspace_id is not None and args.workspace_id > 0:
        run("i3-msg", f"[con_id={args.workspace_id}] focus")
    else:
        parser.error("workspace requires a positive i3 container ID")


if __name__ == "__main__":
    main()
