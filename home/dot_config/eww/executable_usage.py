#!/usr/bin/env python3
"""Read provider quota metadata only; never starts an inference turn."""

import fcntl
import json
import math
import os
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "eww-usage"
TTL = 180


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def window(label, used, reset):
    if not number(used) or not 0 <= used <= 100:
        return None
    reset = reset if number(reset) and reset > 0 else None
    return {
        "label": label,
        "used": round(used, 1),
        "remaining": round(100 - used, 1),
        "resets_at": reset,
    }


def codex_windows(result):
    if not isinstance(result, dict):
        raise TypeError("Invalid quota response")
    buckets = result.get("rateLimitsByLimitId")
    if not isinstance(buckets, dict) or not buckets:
        buckets = {"Codex": result.get("rateLimits")}
    output = []
    for name, bucket in buckets.items():
        if not isinstance(bucket, dict):
            continue
        title = bucket.get("limitName") or name
        for key in ("primary", "secondary"):
            data = bucket.get(key)
            if not isinstance(data, dict):
                continue
            minutes = data.get("windowDurationMins")
            duration = key
            if number(minutes) and minutes > 0:
                duration = (
                    f"{minutes / 1440:g}d"
                    if minutes % 1440 == 0
                    else f"{minutes / 60:g}h"
                    if minutes % 60 == 0
                    else f"{minutes:g}m"
                )
            item = window(
                f"{title} · {duration}", data.get("usedPercent"), data.get("resetsAt")
            )
            if item:
                output.append(item)
    return output


def fetch_codex():
    selector = None
    process = None

    def send(message):
        assert process is not None and process.stdin is not None
        process.stdin.write((json.dumps(message) + "\n").encode())
        process.stdin.flush()

    def receive(request_id):
        nonlocal pending
        assert selector is not None
        while time.monotonic() < deadline:
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                reply = json.loads(line)
                if isinstance(reply, dict) and reply.get("id") == request_id:
                    if "error" in reply:
                        raise ValueError("Quota unavailable; check Codex login")
                    return reply.get("result")
            if not selector.select(max(0, deadline - time.monotonic())):
                break
            assert process is not None and process.stdout is not None
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                raise ValueError("Codex server closed")
            pending += chunk
            if len(pending) > 2_000_000:
                raise ValueError("Oversized response")
        raise TimeoutError("Codex quota request timed out")

    try:
        process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        assert (
            process is not None
            and process.stdin is not None
            and process.stdout is not None
        )
        deadline = time.monotonic() + 15
        pending = b""
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        send(
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "eww_quota",
                        "title": "Desktop quota",
                        "version": "1.0",
                    }
                },
            }
        )
        receive(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "account/rateLimits/read", "params": {}})
        return codex_windows(receive(2))
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)
            if process.stdin is not None:
                process.stdin.close()
            if process.stdout is not None:
                process.stdout.close()


def display(data, fallback):
    now = time.time()
    updated = data.get("updated_at")
    updated = updated if number(updated) else 0
    windows = []
    for raw in data.get("windows", []) if isinstance(data.get("windows"), list) else []:
        if not isinstance(raw, dict):
            continue
        item = window(
            str(raw.get("label", "Quota")), raw.get("used"), raw.get("resets_at")
        )
        if item:
            reset = item["resets_at"]
            item["reset_label"] = (
                time.strftime("%a %H:%M", time.localtime(reset))
                if reset and reset < 253402300800
                else "Unknown"
            )
            windows.append(item)
    stale = bool(windows) and (
        now - updated > TTL * 2
        or bool(data.get("error"))
        or any(w["resets_at"] and w["resets_at"] <= now for w in windows)
    )
    status = "Cached · stale" if stale else "Current" if windows else fallback
    return {
        "available": bool(windows),
        "windows": windows,
        "status": status,
        "updated_at": updated,
        "stale": stale,
    }


def read_usage(refresh=False):
    CACHE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (CACHE / "codex.lock").open("a") as lock:
        os.chmod(CACHE / "codex.lock", 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            data = load(CACHE / "codex.json")
            checked = data.get("checked_at", 0)
            if refresh or not number(checked) or time.time() - checked >= TTL:
                try:
                    windows = fetch_codex()
                    data = {"windows": windows, "updated_at": time.time()}
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    TimeoutError,
                    subprocess.SubprocessError,
                ):
                    data["error"] = True
                data["checked_at"] = time.time()
                save(CACHE / "codex.json", data)
    return {
        "codex": display(load(CACHE / "codex.json"), "Unavailable · check Codex login"),
        "claude": display(
            load(CACHE / "claude.json"), "Waiting for Claude status line"
        ),
    }


def terminate(signum, _frame):
    # Eww stops poll commands on reload/close. Unwind fetch_codex's cleanup,
    # and ignore repeated termination while the child process is being reaped.
    signal.signal(signum, signal.SIG_IGN)
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGHUP, terminate)
    print(json.dumps(read_usage("--refresh" in sys.argv)))
