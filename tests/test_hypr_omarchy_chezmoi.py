"""Exercise chezmoi in disposable directories; never activate the real desktop."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROFILE = (
    "hyprland.lua",
    "appearance.lua",
    "omarchy-looknfeel.lua",
    "omarchy-input-env.lua",
    "omarchy-windows.lua",
    "keyboard.lua",
    "keys.tsv",
    "executable_keymap.py",
    "scratchpads.py",
    "capture.py",
    "startup.py",
    "desktop_actions.py",
    "native_shell.py",
    "theme_request.py",
    "rofi.rasi",
    "hyprlock.conf",
)
ENTRYPOINT = Path("dot_local/bin/executable_omarchy-inspired-session")


class HyprOmarchyChezmoiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="omarchy-chezmoi-",
            dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None,
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.destination = self.root / "destination"
        self.source.mkdir()
        self.destination.mkdir()
        self.config = self.root / "config.toml"
        self.config.write_text(
            '[data.machine]\nprofile = "personal"\nwm = "i3"\nsecrets = false\n'
        )
        shutil.copyfile(
            REPO / "home/.chezmoiignore.tmpl", self.source / ".chezmoiignore"
        )
        for relative in [
            *(Path("dot_config/hypr-omarchy") / n for n in PROFILE),
            ENTRYPOINT,
        ]:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / "home" / relative, target)
        # A regression in the include filter must fail, never run a desktop hook.
        (self.source / "run_once_after_probe.sh").write_text("#!/bin/sh\nexit 99\n")

    def command(
        self,
        *args,
        os_name="linux",
        distro="arch",
        profile="personal",
        wm="i3",
        home="/home/ll931217",
        arch="amd64",
    ):
        data = {
            "chezmoi": {
                "os": os_name,
                "arch": arch,
                "homeDir": home,
                "osRelease": {"id": distro},
            },
            "machine": {"profile": profile, "wm": wm, "secrets": False},
        }
        return subprocess.run(
            [
                "chezmoi",
                "--source",
                str(self.source),
                "--destination",
                str(self.destination),
                "--config",
                str(self.config),
                "--persistent-state",
                str(self.root / "state.db"),
                "--cache",
                str(self.root / "cache"),
                "--refresh-externals=never",
                "--skip-secrets",
                "--no-tty",
                "--override-data",
                json.dumps(data),
                *args,
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )

    def test_real_managed_targets_follow_host_and_profile_guard(self):
        cases = (
            ({}, True),
            ({"wm": "hyprland"}, True),
            ({"profile": "work"}, False),
            ({"distro": "debian"}, False),
            ({"os_name": "darwin", "distro": ""}, False),
            ({"os_name": "android", "distro": ""}, False),
            ({"home": "/home/another-user"}, False),
            ({"arch": "arm64"}, False),
        )
        for values, allowed in cases:
            with self.subTest(values=values):
                targets = self.command(
                    "managed", "--include=files", "--path-style=relative", **values
                ).stdout.splitlines()
                self.assertEqual(".config/hypr-omarchy/startup.py" in targets, allowed)
                self.assertEqual(
                    ".local/bin/omarchy-inspired-session" in targets, allowed
                )

    def test_apply_restores_bytes_and_executable_without_deleting_unmanaged_files(self):
        unmanaged = self.destination / ".config/hypr-omarchy/.git/local-marker"
        unmanaged.parent.mkdir(parents=True)
        unmanaged.write_text("local repository must survive")
        self.command("apply", "--include=files,dirs")
        for name in PROFILE:
            target_name = name.removeprefix("executable_")
            expected = self.source / "dot_config/hypr-omarchy" / name
            target = self.destination / ".config/hypr-omarchy" / target_name
            self.assertEqual(target.read_bytes(), expected.read_bytes(), target_name)
        entrypoint = self.destination / ".local/bin/omarchy-inspired-session"
        self.assertEqual(
            entrypoint.read_bytes(), (self.source / ENTRYPOINT).read_bytes()
        )
        self.assertTrue(entrypoint.stat().st_mode & 0o100)
        self.assertTrue(
            (self.destination / ".config/hypr-omarchy/keymap.py").stat().st_mode & 0o100
        )
        self.assertEqual(unmanaged.read_text(), "local repository must survive")
        self.assertEqual(self.command("diff", "--include=files").stdout, "")
        keymap = self.destination / ".config/hypr-omarchy/keymap.py"
        keymap.write_text(keymap.read_text() + "\n# synthetic preview drift\n")
        preview = self.command(
            "diff",
            "--recursive",
            "--include=files",
            str(self.destination / ".config/hypr-omarchy"),
        ).stdout
        self.assertIn("synthetic preview drift", preview)

    def test_private_and_generated_source_entries_cannot_be_deployed(self):
        for relative in (
            "dot_local/state/omarchy-inspired/private-marker",
            "dot_local/share/omarchy-inspired/private-marker",
            "dot_config/hypr-omarchy/__pycache__/private-marker",
            "dot_config/hypr-omarchy/.git/private-marker",
            "dot_config/hypr-omarchy/hyprland.lua.backup.fixture",
        ):
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SYNTHETIC-PRIVATE-MARKER")
        targets = self.command(
            "managed", "--include=files", "--path-style=relative"
        ).stdout
        self.assertNotIn("private-marker", targets)
        self.assertNotIn("backup.fixture", targets)
        self.command("apply", "--include=files,dirs")
        self.assertFalse((self.destination / ".local/state/omarchy-inspired").exists())
        self.assertFalse((self.destination / ".local/share/omarchy-inspired").exists())


if __name__ == "__main__":
    unittest.main()
