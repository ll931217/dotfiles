"""Session-scoped Hyprland actions. Run --list for the key registry API."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.modules.setdefault("desktop_actions", sys.modules[__name__])
HOME = Path("/home/ll931217")
WRAPPER = HOME / ".local/bin/omarchy-inspired-session"
AI = HOME / ".local/bin/omarchy-ai"
NATIVE_LAUNCHER = HOME / ".local/share/omarchy-inspired/native-ui/launcher.py"
DESCRIPTIONS = {
    "launcher": "Toggle Vicinae launcher; report command failures without opening another launcher",
    "launcher-hub": "Explicit Rofi hub: Apps / Windows / Run / Files / Power / AI / Clipboard / Themes",
    "clipboard": "Open native clipboard history picker",
    "themes": "Open native theme picker",
    "windows": "Choose an actual Hyprland window by index",
    "control-center": "Audio / network / Bluetooth controls and display information",
    "notification-history": "Open full native notifications; verified legacy Dunst history fallback",
    "notification-pause": "Toggle full native DND; verified legacy Dunst pause fallback",
    "scratch-terminal": "Toggle st terminal scratchpad (XWayland required)",
    "scratch-droid": "Toggle Droid in st (XWayland required)",
    "scratch-purple": "Toggle Purple in st (XWayland required)",
    "scratch-spotify": "Reuse or launch Spotify scratchpad",
    "scratch-chatgpt": "Reuse or launch ChatGPT desktop, centered at 90% size",
    "scratch-cycle": "Cycle existing scratchpads; never spawn an app",
    "screenshot-editor": "Select region with slurp, capture with grim, annotate/copy/save in Satty",
    "credential-copy": "Explicitly copy private credential using wl-copy; never print it",
    "password-picker": "Bitwarden picker: clipboard only, clears after 30s; no autotype",
    "record-start": "Record primary output plus system audio, never microphone",
    "record-stop": "Stop only this session recorder after PID identity verification",
    "wallpaper-normal": "Random wallpaper from ~/.wallpapers; running awww/swww required",
    "wallpaper-private": "Explicit private wallpaper; running awww/swww required",
    "wallpaper-enhanced": "Enhanced wallpaper from existing ~/.wallpapers_cache; no downloads",
    "volume-up": "Increase output volume 5%, capped at 100%, with progress notification",
    "volume-down": "Decrease output volume 5% with progress notification",
    "volume-mute": "Toggle output mute with progress notification",
    "brightness-up": "Show external-monitor brightness controls guidance",
    "brightness-down": "Show external-monitor brightness controls guidance",
    "media-play-pause": "Toggle media playback",
    "media-pause": "Pause media only; never resume",
    "media-next": "Next media track",
    "media-previous": "Previous media track",
    "power-menu": "Confirmed Cancel / Lock / Logout / Reboot / Poweroff; no suspend",
    "unsupported-parent": "Explain unsupported i3 parent-container focus",
    "reload": "Reload configuration only; never restart or log out",
}
AI_COMMANDS = {
    "default-agent": ["agent"],
    "select": ["select"],
    "chatgpt-web": ["chatgpt"],
    "grok-web": ["grok"],
    "tmux": ["layout", "dev"],
    "ocr": ["ocr"],
}
VOICE = {
    "voice-transcribe": "--toggle-transcription",
    "voice-post-process": "--toggle-post-process",
    "voice-cancel": "--cancel",
}
ACTIONS = {"desktop:" + key: value for key, value in DESCRIPTIONS.items()}
ACTIONS["ai:panel"] = (
    "Open native AI panel; omarchy-ai panel remains available for auth/consent"
)
ACTIONS.update(
    {
        "ai:" + key: "Open AI workflow: " + " ".join(value)
        for key, value in AI_COMMANDS.items()
    }
)
ACTIONS.update(
    {
        "ai:" + key: "Handy " + value + " (explicit user action only)"
        for key, value in VOICE.items()
    }
)


class ActionError(RuntimeError):
    pass


def executable(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise ActionError(
            f"Missing {name}; install or configure {name}, then retry this action."
        )
    return found


def address(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", value):
        raise ActionError(
            "Invalid Hyprland window address; refresh the window list and retry."
        )
    return value


def clean(value: Any) -> str:
    return "".join(c if c.isprintable() else " " for c in str(value))[:200]


class Session:
    def run(self, args, *, input=None, check=True, env=None):
        try:
            result = subprocess.run(
                [str(a) for a in args],
                input=input,
                capture_output=True,
                text=not isinstance(input, bytes),
                timeout=None
                if Path(str(args[0])).name
                in ("rofi", "rofi-rbw", "slurp", "satty", "omarchy-inspired-session")
                else 30,
                env=env,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ActionError(
                f"Cannot run {Path(args[0]).name}; check its installation/session and retry."
            ) from exc
        if check and result.returncode:
            raise ActionError(
                f"{Path(args[0]).name} failed (exit {result.returncode}); check its session/service and retry."
            )
        return result

    def query(self, name):
        try:
            return json.loads(self.run(["hyprctl", "-j", name]).stdout)
        except (ValueError, TypeError) as exc:
            raise ActionError(
                f"Invalid hyprctl {name} JSON; log into the native Hyprland session and retry."
            ) from exc

    def require_context(self):
        if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE") or not os.environ.get(
            "WAYLAND_DISPLAY"
        ):
            raise ActionError(
                "No active Hyprland context; log into the Omarchy-inspired Hyprland session, then retry. Use --dry-run to preview safely."
            )
        monitors = self.query("monitors")
        if not isinstance(monitors, list) or not monitors:
            raise ActionError(
                "Hyprland has no active monitors; log into the physical Hyprland session and retry."
            )

    def dispatch(self, expression):
        # Hyprland v0.56.2 LuaBindingsDispatchers.cpp and HyprCtl.cpp define this API.
        result = self.run(["hyprctl", "dispatch", expression])
        if not result.stdout.strip().startswith("ok"):
            raise ActionError(
                "Hyprland rejected the native dispatch; check the 0.56 Lua configuration and retry."
            )

    def notify(self, title, body, progress=None):
        if shutil.which("notify-send"):
            args = [
                "notify-send",
                "-a",
                "Hyprland actions",
                "-h",
                "string:x-dunst-stack-tag:hypr-actions",
            ]
            if progress is not None:
                args += ["-h", f"int:value:{progress}"]
            self.run(args + [title, body], check=False)
        print(f"{title}: {body}")

    def menu(self, prompt, entries):
        result = self.run(
            [
                "rofi",
                "-config",
                SOURCE / "rofi.rasi",
                "-dmenu",
                "-i",
                "-no-custom",
                "-format",
                "i",
                "-p",
                prompt,
            ],
            input="\n".join(clean(e) for e in entries),
            check=False,
        )
        if result.returncode == 1:
            print(f"{prompt}: cancelled; nothing changed.")
            return None
        if result.returncode or not re.fullmatch(r"\d+\s*", result.stdout):
            raise ActionError(
                "Rofi did not return a selection index; close this picker and retry."
            )
        index = int(result.stdout)
        if index >= len(entries):
            raise ActionError(
                "Rofi returned an out-of-range index; reopen the picker and retry."
            )
        return index

    def runtime(self):
        root = Path(os.environ.get("XDG_RUNTIME_DIR", "/nonexistent"))
        if (
            not root.is_dir()
            or root.is_symlink()
            or root.stat().st_uid != os.getuid()
            or stat.S_IMODE(root.stat().st_mode) & 0o077
        ):
            raise ActionError(
                "XDG_RUNTIME_DIR must be your private runtime directory; log into Hyprland normally and retry."
            )
        token = hashlib.sha256(
            os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "").encode()
        ).hexdigest()[:20]
        directory = root / ("hypr-omarchy-actions-" + token)
        directory.mkdir(mode=0o700, exist_ok=True)
        if (
            directory.is_symlink()
            or directory.stat().st_uid != os.getuid()
            or stat.S_IMODE(directory.stat().st_mode) & 0o077
        ):
            raise ActionError(
                "Unsafe action state directory; fix its ownership/permissions before retrying."
            )
        return directory

    @contextmanager
    def locked(self, name):
        path = self.runtime() / (name + ".lock")
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def save(self, path, data):
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".state-")
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(data, stream)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def windows(session):
    clients = session.query("clients")
    if not clients:
        session.notify(
            "Windows", "No windows open; launch an app with Super+D (Vicinae)."
        )
        return
    index = session.menu(
        "Windows — choose to focus",
        [f"{clean(c.get('class', ''))} — {clean(c.get('title', ''))}" for c in clients],
    )
    if index is None:
        return
    target = address(clients[index]["address"])
    if not any(c.get("address") == target for c in session.query("clients")):
        raise ActionError(
            "Selected window closed; reopen Super+Tab and select another window."
        )
    session.dispatch(f'hl.dsp.focus({{window="address:{target}"}})')
    print("Windows: focused selected window.")


def launch(session, command, label):
    import native_shell

    executable(str(command[0]))
    if command[2:3] == [native_shell.FULL_CLIENT] and command[-1] == "--themes":
        worker = SOURCE / "theme_request.py"
        if not worker.is_file():
            raise ActionError(
                "Theme request supervisor missing; restore theme_request.py before retrying."
            )
        subprocess.Popen(
            ["/usr/bin/python", "-I", "-B", str(worker)],
            stdin=subprocess.DEVNULL,
            stdout=None,
            stderr=None,
            start_new_session=True,
        )
        print("Theme picker requested; completion or failure will be reported.")
        return
    if command[2:3] == [native_shell.FULL_CLIENT] and command[-1] != "--themes":
        # Short-lived IPC clients must finish successfully; never retry another UI.
        session.run(command)
        print(f"{label}: full native request accepted.")
        return
    subprocess.Popen(
        [str(x) for x in command],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    session.notify(label, "Opened in this Hyprland session.")


def power(session):
    options = [
        "Cancel — keep working",
        "Lock — login password to unlock",
        "Logout — end this Hyprland session",
        "Reboot — restart computer",
        "Poweroff — shut down computer",
    ]
    choice = session.menu("Power — no automatic suspend", options)
    if choice in (None, 0):
        if choice == 0:
            print("Power: cancelled; nothing changed.")
        return
    label = options[choice].split(" — ")[0]
    if (
        session.menu(
            f"Confirm {label}? Save your work first.",
            ["Cancel — keep working", f"Confirm {label}"],
        )
        != 1
    ):
        print(f"{label}: cancelled; nothing changed.")
        return
    commands = {
        1: [WRAPPER, "--lock"],
        2: [WRAPPER, "--logout"],
        3: ["systemctl", "reboot"],
        4: ["systemctl", "poweroff"],
    }
    session.run(commands[choice])
    print(f"{label}: request accepted for this session/computer.")


def hub(session):
    choice = session.menu(
        "Launcher — native Hyprland hub",
        ["Apps", "Windows", "Run", "Files", "Power", "AI", "Clipboard", "Themes"],
    )
    if choice is None:
        return
    if choice in (0, 2):
        mode = "drun" if choice == 0 else "run"
        result = session.run(
            ["rofi", "-config", SOURCE / "rofi.rasi", "-show", mode], check=False
        )
        if result.returncode not in (0, 1):
            raise ActionError(
                "Rofi launcher failed; check the Wayland Rofi installation and retry."
            )
        print(
            "Launcher: selection finished or cancelled; no other Rofi window was closed."
        )
    elif choice == 1:
        windows(session)
    elif choice == 3:
        launch(session, ["thunar", HOME], "Files")
    elif choice == 4:
        power(session)
    elif choice == 5:
        perform(session, "ai:panel")
    elif choice == 6:
        perform(session, "desktop:clipboard")
    elif choice == 7:
        perform(session, "desktop:themes")


def controls(session):
    choice = session.menu(
        "Controls",
        [
            "Audio — volume / mute / devices",
            "Network — connections",
            "Bluetooth — devices",
            "Displays — output information / brightness guidance",
        ],
    )
    if choice is None:
        return
    if choice < 3:
        tools = [
            ("pwvucontrol", "pavucontrol"),
            ("iwgtk",),
            ("blueman-manager", "bluetoothctl"),
        ][choice]
        tool = next((x for x in tools if shutil.which(x)), None)
        if not tool:
            raise ActionError(
                f"Missing {' or '.join(tools)}; install a native control app, then retry Controls."
            )
        command = [tool] if tool != "bluetoothctl" else [executable("st"), "-e", tool]
        launch(
            session,
            command,
            [
                "Audio controls",
                "Wi-Fi connections (existing IWD)",
                "Bluetooth controls (type help for commands)",
            ][choice],
        )
    else:
        lines = [
            f"{clean(m['name'])}: {m['width']}×{m['height']}, scale {m['scale']}"
            for m in session.query("monitors")
        ]
        session.menu(
            "Displays — informational; use monitor OSD for brightness",
            lines
            + ["External brightness: use monitor buttons / OSD; no brightnessctl"],
        )
        print("Displays: information shown; no monitor configuration changed.")


def volume(session, action):
    executable("wpctl")
    if action == "volume-mute":
        session.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    else:
        session.run(
            [
                "wpctl",
                "set-volume",
                "-l",
                "1",
                "@DEFAULT_AUDIO_SINK@",
                "5%+" if action == "volume-up" else "5%-",
            ]
        )
    value = session.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]).stdout
    match = re.search(r"Volume:\s*([\d.]+)", value)
    if not match:
        raise ActionError(
            "Audio changed but volume status is unreadable; open Super+B → Audio to check it."
        )
    percent = round(float(match[1]) * 100)
    session.notify(
        "Audio",
        f"{'Muted' if 'MUTED' in value else 'Volume'}: {percent}%",
        max(0, min(100, percent)),
    )


def wallpaper(session, action):
    backend = next((tool for tool in ("awww", "swww") if shutil.which(tool)), None)
    if not backend:
        raise ActionError(
            "Wallpaper needs awww or swww; restore the installed session wallpaper tools, then retry. No daemon or wallpaper was changed."
        )
    if session.run([backend, "query"], check=False).returncode:
        raise ActionError(
            f"{backend} daemon is not ready on this display; check the Omarchy-inspired session helpers before retrying. Do not stop unrelated wallpaper daemons."
        )
    folder = {
        "wallpaper-normal": HOME / ".wallpapers",
        "wallpaper-private": HOME / ".pvt/NSFW",
        "wallpaper-enhanced": HOME / ".wallpapers_cache",
    }[action]
    candidates = [
        p
        for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    ]
    if not candidates:
        raise ActionError(
            f"No supported wallpaper in {folder}; add an image there, then retry. Enhanced mode uses the existing cache, not network downloads."
        )
    session.run([backend, "img", random.choice(candidates)])
    session.notify(
        "Wallpaper",
        f"{action.removeprefix('wallpaper-')} wallpaper applied from {folder}; selected filename kept private.",
    )


def perform(session, action):
    category, name = action.split(":", 1)
    if category == "ai":
        if name in VOICE:
            command = {
                "voice-transcribe": "handy",
                "voice-post-process": "handy-postprocess",
                "voice-cancel": "handy-cancel",
            }[name]
            reply = session.run([AI, command], check=False)
            if reply.returncode:
                raise ActionError(
                    reply.stderr.strip()
                    or "Handy control failed. Open Handy, then retry its shortcut."
                )
            session.notify(
                "Handy",
                reply.stdout.strip()
                or "Handy control requested; check its current status.",
            )
        elif name == "panel":
            import native_shell

            native_shell.panel(session, "ai", "AI panel")
        else:
            launch(session, [AI, "--notify-errors", *AI_COMMANDS[name]], "AI " + name)
    elif name in ("clipboard", "themes"):
        import native_shell

        native_shell.panel(session, name, name.capitalize())
    elif name.startswith("scratch-"):
        import scratchpads

        scratchpads.toggle(session, name.removeprefix("scratch-"))
    elif name in ("screenshot-editor", "record-start", "record-stop"):
        import capture

        capture.perform(session, name)
    elif name == "launcher":
        session.run([executable("vicinae"), "toggle"])
        print("Vicinae: toggle request accepted.")
    elif name == "launcher-hub":
        hub(session)
    elif name == "windows":
        windows(session)
    elif name == "control-center":
        controls(session)
    elif name == "power-menu":
        power(session)
    elif name.startswith("volume-"):
        volume(session, name)
    elif name.startswith("brightness-"):
        session.notify(
            "External display brightness",
            "Use the monitor buttons / OSD. Super+B → Displays shows output information. No brightnessctl or brightness change was attempted.",
        )
    elif name.startswith("notification-"):
        import native_shell

        native_shell.notifications(session, name)
    elif name.startswith("wallpaper-"):
        wallpaper(session, name)
    elif name.startswith("media-"):
        session.run(["playerctl", name.removeprefix("media-")])
        print(f"Media: {name.removeprefix('media-')} requested.")
    elif name == "unsupported-parent":
        session.notify(
            "Parent focus unsupported",
            "Hyprland dwindle has no i3 parent container. Use Super+H/J/K/L for window focus; grouping is not parent focus.",
        )
    elif name == "reload":
        session.run(["hyprctl", "reload"])
        session.notify(
            "Configuration reloaded",
            "Closest safe restart equivalent: windows/session kept; no compositor restart or logout.",
        )
    elif name == "credential-copy":
        executable("wl-copy")
        try:
            payload = (HOME / ".pvt/pw").read_bytes()
        except OSError as exc:
            raise ActionError(
                "Credential source unavailable; restore ~/.pvt/pw permissions/content, then retry Super+O."
            ) from exc
        session.run(
            ["wl-copy", "--sensitive", "--paste-once", "--type", "text/plain"],
            input=payload,
        )
        del payload
        session.notify(
            "Credential",
            "Copied to Wayland clipboard without printing or saving a copy. Clipboard managers may retain it; clear clipboard/history when finished.",
        )
    elif name == "password-picker":
        for tool in ("rofi-rbw", "rbw", "wl-copy", "rofi"):
            executable(tool)
        session.run(
            [
                "rofi-rbw",
                "--selector",
                "rofi",
                "--clipboarder",
                "wl-copy",
                "--action",
                "copy",
                "--target",
                "password",
                "--clear-after",
                "30",
                "--keybindings",
                "Alt+c:copy:password",
                "--menu-keybindings",
                "Alt+c:copy",
                "--selector-args",
                f"-config {SOURCE / 'rofi.rasi'}",
            ]
        )
        print(
            "Password picker: finished; copy-only mode, clipboard expiry 30 seconds, no autotype requested."
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Native Hyprland desktop actions. No actions run by --help, --list or --dry-run."
    )
    parser.add_argument(
        "action", nargs="?", help="Full desktop:ACTION or ai:ACTION from --list"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List supported IDs and their effects without reading session/private state",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explain an action; no subprocesses, app launches, IPC, clipboard or private reads",
    )
    args = parser.parse_args(argv)
    if args.list:
        print(
            "\n".join(f"{key}\t{description}" for key, description in ACTIONS.items())
        )
        return 0
    if args.action not in ACTIONS:
        parser.error(
            "unknown or missing action; use --list to choose a full desktop:ACTION or ai:ACTION ID"
        )
    if args.dry_run:
        print(
            f"DRY RUN {args.action}: {ACTIONS[args.action]}. No action executed; no session/private state read."
        )
        return 0
    session = Session()
    try:
        session.require_context()
        perform(session, args.action)
        return 0
    except (
        ActionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.TimeoutExpired,
    ) as exc:
        message = f"Action {args.action} failed: {exc}"
        print(message, file=sys.stderr)
        if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY"):
            try:
                session.notify("Hyprland action needs attention", message)
            except ActionError:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
