#!/usr/bin/python
"""Read-only keyboard registry and session help; never executes actions."""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

MANIFEST = Path(__file__).with_name("keys.tsv")
FIELDS = ("mode", "chord", "action", "label", "compatibility")
MODES = {"default", "resize", "gaps", "gaps-inner", "gaps-outer"}
MODIFIERS = {
    "super": "Super",
    "mod4": "Super",
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
}
ORDER = ("Super", "Ctrl", "Alt", "Shift")
NATIVE_ACTION = re.compile(
    r"native:(?:close|fullscreen|float|focus-layer|reload|"
    r"(?:focus|move):(?:left|right|up|down)|(?:workspace|send):(?:[1-9]|10)|"
    r"mode:(?:default|resize|gaps|gaps-inner|gaps-outer)|"
    r"resize:(?:-10|0|10):(?:-10|0|10)|"
    r"gaps:(?:inner|outer):(?:current|all):(?:plus|minus|zero))\Z"
)


def normalize_chord(chord: str) -> str:
    parts = [part.strip() for part in chord.split("+")]
    if not parts or not re.fullmatch(r"[A-Za-z0-9_]+", parts[-1]):
        raise ValueError(f"invalid chord {chord!r}; use Super+Shift+x or plus")
    modifiers = []
    for part in parts[:-1]:
        modifier = MODIFIERS.get(part.lower())
        if modifier is None or modifier in modifiers:
            raise ValueError(
                f"invalid modifier {part!r} in {chord!r}; use each modifier once"
            )
        modifiers.append(modifier)
    key = parts[-1].lower()
    key = {"enter": "return", "esc": "escape"}.get(key, key)
    return "+".join([item for item in ORDER if item in modifiers] + [key])


def valid_action(action):
    if action.startswith("native:"):
        return NATIVE_ACTION.fullmatch(action) is not None
    if action.startswith("session:"):
        return action in {"session:terminal", "session:lock", "session:logout"}
    return re.fullmatch(r"(?:desktop|ai):[a-z][a-z0-9-]*", action) is not None


def load_registry(path=MANIFEST):
    rows, seen = [], set()
    try:
        with Path(path).open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if tuple(reader.fieldnames or ()) != FIELDS:
                raise ValueError(
                    "invalid header; use mode, chord, action, label, compatibility separated by tabs"
                )
            for line, row in enumerate(reader, 2):
                if None in row or any(
                    not (row.get(field) or "").strip() for field in FIELDS
                ):
                    raise ValueError(
                        f"line {line}: missing or extra field; supply exactly five nonempty tab-separated fields"
                    )
                mode, chord, action = row["mode"], row["chord"], row["action"]
                if mode not in MODES:
                    raise ValueError(
                        f"line {line}: unknown mode {mode!r}; use {', '.join(sorted(MODES))}"
                    )
                identity = (mode, normalize_chord(chord))
                if identity in seen:
                    raise ValueError(
                        f"line {line}: duplicate {mode} {chord}; remove or change the duplicate chord"
                    )
                if not valid_action(action):
                    raise ValueError(
                        f"line {line}: invalid action {action!r}; use a supported native:, session:, desktop: or ai: action"
                    )
                seen.add(identity)
                rows.append(row)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise ValueError(
            f"{path}: {error}. Fix the registry, then retry --help."
        ) from error
    if not rows:
        raise ValueError(
            f"{path}: empty registry; add bindings below the five-column header, then retry --help."
        )
    return rows


def render_help(rows):
    lines = [
        "Hyprland — Omarchy-inspired: separate opt-in desktop; i3 remains available.",
        "Start: log out when ready; select 'Hyprland — Omarchy-inspired' in SDDM.",
        "Return: open Super+Shift+q power menu, confirm logout, then select i3 in SDDM.",
        "Session controls: omarchy-inspired-session --start | --check [LUA_CONFIG] | --terminal | --lock | --logout | --help",
        "Idle locking: OFF. Test Super+Shift+x and password unlock before manually enabling hypridle. No automatic suspend.",
        "Super+l focuses right; Super+Shift+x locks. Reload never logs out.",
        "Super+d: toggle Vicinae (native Wayland); server starts with this Hyprland session.",
        "Handy: Super+Ctrl+v plain; Super+Ctrl+b post-process; Super+Ctrl+Escape cancel (new).",
        "Escape cancels Handy inside its app only; there is no global Escape binding.",
        "Modes: Super+r resize; Super+Shift+g gaps, then O outer / I inner.",
        "In gap modes: US = current, + (Shift+=) all; minus/0 current; Shift variants change all workspaces.",
        "Enter/Escape exits a mode; gap values persist until config reload.",
        "Mouse: Super+left drag / Super+right resize are configured by the main desktop module.",
        "Application actions require desktop_actions.py; this help never runs them.",
        f"Registry: {MANIFEST}",
    ]
    current_mode = None
    for row in rows:
        if row["mode"] != current_mode:
            current_mode = row["mode"]
            lines.append(f"\n[{current_mode}]")
        lines.append(
            f"  {row['chord']:<26} {row['label']} [{row['action']}]\n    {row['compatibility']}"
        )
    return "\n".join(lines)


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument("--manifest", type=Path, default=MANIFEST)
    selected, _ = preliminary.parse_known_args(arguments)
    try:
        rows = load_registry(selected.manifest)
    except ValueError as error:
        print(f"keymap: {error}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(
        description="Read keyboard bindings and safe session controls without executing actions.",
        epilog=render_help(rows),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="read a different five-column TSV registry (read-only)",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--list-json",
        action="store_true",
        help="print every binding as JSON; never run actions",
    )
    output.add_argument(
        "--describe",
        nargs=2,
        metavar=("MODE", "CHORD"),
        help="explain a chord, for example --describe default Super+l",
    )
    options = parser.parse_args(arguments)
    if options.list_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif options.describe:
        mode, chord = options.describe
        try:
            identity = (mode, normalize_chord(chord))
        except ValueError as error:
            parser.error(str(error))
        found = [
            row
            for row in rows
            if (row["mode"], normalize_chord(row["chord"])) == identity
        ]
        if not found:
            parser.error(
                f"no binding for {mode} {chord}; run --help to choose a listed mode and chord"
            )
        row = found[0]
        print(
            f"{row['mode']} {row['chord']}: {row['label']}\nAction: {row['action']}\nCompatibility: {row['compatibility']}"
        )
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
