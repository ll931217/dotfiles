#!/usr/bin/python3 -I
"""Constrained networkd route preferences; inspect never changes network state."""

import argparse
import configparser
import fcntl
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path("/etc/systemd/network")
DROPIN = "90-eww-preference.conf"
MARKER = "# Managed by eww-network-preference\n"
ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}


def run(*args):
    return subprocess.check_output(args, text=True, timeout=20, env=ENV)


def trusted(path, directory=False):
    """Every component must be root-owned and not writable by other users."""
    for item in reversed((path, *path.parents)):
        info = item.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
            raise ValueError("Untrusted network configuration path")
    info = path.stat()
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode):
        raise ValueError("Unexpected network configuration file type")


def destination(link):
    name = link.get("Name", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,14}", name):
        raise ValueError("Invalid interface name")
    path = Path(link.get("NetworkFile", ""))
    if path.parent != ROOT or not re.fullmatch(r"[A-Za-z0-9_.-]+\.network", path.name):
        raise ValueError("Only local networkd DHCP profiles are supported")
    trusted(path)
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.read_string(path.read_text())
    if parser.get("Network", "DHCP", fallback="").lower() not in (
        "yes",
        "true",
        "ipv4",
    ):
        raise ValueError("Only DHCP profiles are supported")
    if any(s in parser for s in ("Route", "RoutingPolicyRule", "Bridge", "VRF")):
        raise ValueError("Static or policy routing is managed externally")
    if any(
        parser.has_option("Network", x) for x in ("Gateway", "Bridge", "VRF", "Bond")
    ):
        raise ValueError("Complex network profiles are managed externally")
    target = Path(str(path) + ".d") / DROPIN
    if target.parent.exists():
        trusted(target.parent, directory=True)
        if any(p.name != DROPIN for p in target.parent.iterdir()):
            raise ValueError("Existing profile overrides are managed externally")
    if any(Path(p) != target for p in link.get("NetworkFileDropins", [])):
        raise ValueError("Existing profile overrides are managed externally")
    if target.exists() or target.is_symlink():
        trusted(target)
        if target.read_text() not in (content(50), content(600)):
            raise ValueError("Refusing to replace an unrecognized override")
    return target


def content(metric):
    return f"{MARKER}[DHCPv4]\nRouteMetric={metric}\n\n[IPv6AcceptRA]\nRouteMetric={metric}\n"


def discover():
    links = json.loads(run("/usr/bin/networkctl", "list", "--json=short"))["Interfaces"]
    details = []
    for link in links:
        if link.get("AdministrativeState") == "unmanaged":
            continue
        index = link.get("Index")
        if not isinstance(index, int) or index < 1:
            continue
        details.append(
            json.loads(run("/usr/bin/networkctl", "status", str(index), "--json=short"))
        )
    counts = Counter(d.get("NetworkFile") for d in details)
    candidates = []
    for link in details:
        if (
            link.get("Type") not in ("ether", "wlan")
            or not (Path("/sys/class/net") / link["Name"] / "device").exists()
        ):
            continue
        routes = [
            r for r in link.get("Routes", []) if r.get("DestinationPrefixLength") == 0
        ]
        reason = ""
        try:
            destination(link)
            if counts[link.get("NetworkFile")] != 1:
                raise ValueError("Profile is shared by multiple interfaces")
            if any(
                r.get("Table") != 254
                or r.get("ConfigSource") not in ("DHCPv4", "NDisc")
                for r in routes
            ):
                raise ValueError("Default route is managed externally")
        except (OSError, ValueError, configparser.Error) as error:
            reason = str(error)
        link["eligible"] = not reason
        link["reason"] = reason
        link["metric"] = min(
            (r.get("Priority", 0) for r in routes if r.get("Family") == 2), default=None
        )
        candidates.append(link)
    return candidates


def owned_overrides():
    paths = []
    for path in ROOT.glob("*.network.d/" + DROPIN):
        trusted(path)
        if path.read_text() not in (content(50), content(600)):
            raise ValueError(
                "Unrecognized managed preference; administrator review required"
            )
        paths.append(path)
    return paths


def snapshot():
    links = discover()
    owned = owned_overrides()
    eligible = [x for x in links if x["eligible"]]
    minimum = min((x["metric"] for x in links if x["metric"] is not None), default=None)
    interfaces = []
    for link in links:
        target = Path(str(link.get("NetworkFile", "")) + ".d") / DROPIN
        interfaces.append(
            {
                "index": link["Index"],
                "name": link["Name"],
                "kind": link["Type"],
                "eligible": link["eligible"],
                "connected": link.get("OperationalState") == "routable",
                "metric": link["metric"],
                "current_default": minimum is not None and link["metric"] == minimum,
                "preferred": target in owned and target.read_text() == content(50),
                "reason": link["reason"],
            }
        )
    return {
        "available": len(eligible) >= 2,
        "reset_available": bool(owned),
        "status": "Choose a preferred connection"
        if len(eligible) >= 2
        else "Network managed by host",
        "interfaces": interfaces,
    }


def replace(path, text):
    if text is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(mode=0o755, exist_ok=True)
    trusted(path.parent, directory=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o644)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def apply(selected):
    if os.geteuid() != 0:
        raise PermissionError("Administrator authentication required")
    # This directory and its lock are never controlled by the requesting user.
    lockdir = Path("/run/eww-network-preference")
    lockdir.mkdir(mode=0o700, exist_ok=True)
    trusted(lockdir, directory=True)
    with (lockdir / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        links = discover()
        eligible = [x for x in links if x["eligible"]]
        if selected is not None and (
            len(eligible) < 2 or selected not in [x["Name"] for x in eligible]
        ):
            raise ValueError("Interface preference is unavailable")
        if selected is not None and not any(
            x["Name"] == selected and x.get("OperationalState") == "routable"
            for x in eligible
        ):
            raise ValueError("Connect the interface before preferring it")
        targets = [(destination(x), x) for x in eligible]
        if selected is None:
            targets = [
                (
                    p,
                    next(
                        (
                            x
                            for x in links
                            if str(p.parent) == str(x.get("NetworkFile")) + ".d"
                        ),
                        None,
                    ),
                )
                for p in owned_overrides()
            ]
        old = {p: p.read_text() if p.exists() else None for p, _ in targets}
        changes = [
            (
                p,
                x,
                None
                if selected is None or x is None
                else content(50 if x["Name"] == selected else 600),
            )
            for p, x in targets
        ]
        changes = [(p, x, value) for p, x, value in changes if old[p] != value]
        if not changes:
            return
        try:
            for path, _, value in changes:
                replace(path, value)
            run("/usr/bin/networkctl", "--no-reconfigure", "reload")
            reconfigure(changes)
        except Exception as error:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            for path, _, _ in changes:
                replace(path, old[path])
            try:
                run("/usr/bin/networkctl", "--no-reconfigure", "reload")
                reconfigure(changes)
            except (OSError, RuntimeError, subprocess.SubprocessError):
                raise RuntimeError(
                    "Settings restored but network recovery needs administrator attention"
                ) from error
            raise RuntimeError(
                "Preference failed; previous settings restored"
            ) from error


def reconfigure(changes):
    indices = [str(x["Index"]) for _, x, _ in changes if x is not None]
    if indices:
        run("/usr/bin/networkctl", "reconfigure", *indices)


def cancelled(_signum, _frame):
    raise RuntimeError("Network preference cancelled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inspect", "prefer", "reset"])
    parser.add_argument("interface", nargs="?")
    args = parser.parse_args()
    if args.action != "inspect":
        signal.signal(signal.SIGTERM, cancelled)
    try:
        if args.action == "prefer":
            if not args.interface:
                raise ValueError("Interface required")
            apply(args.interface)
        elif args.interface:
            raise ValueError("Unexpected interface argument")
        elif args.action == "reset":
            apply(None)
        else:
            print(json.dumps(snapshot()))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        configparser.Error,
        subprocess.SubprocessError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
