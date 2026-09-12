import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest


PROFILE = Path(__file__).parent


class ProfileTests(unittest.TestCase):
    def test_shared_palette_has_light_foreground(self):
        palette = (PROFILE / "colors.sh").read_text()
        self.assertIn("export ITEM_COLOR=0xfff2ecdd", palette)
        self.assertIn("source", (PROFILE / "appearance.sh").read_text())

    def setUp(self):
        self.config = tomllib.loads((PROFILE / "aerospace.toml").read_text())
        self.bindings = self.config["mode"]["main"]["binding"]

    def test_typing_and_native_command_shortcuts_are_not_intercepted(self):
        for shortcut in self.bindings:
            self.assertTrue(shortcut.startswith("alt-"), shortcut)

    def test_current_config_version_has_stable_workspace_order(self):
        self.assertEqual(self.config["config-version"], 2)
        self.assertEqual(
            self.config["persistent-workspaces"],
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "B", "I", "S", "T"],
        )

    def test_i3_workspace_back_and_forth_and_move(self):
        for key, workspace in [(str(n), str(n)) for n in range(1, 10)] + [("0", "10")]:
            self.assertEqual(self.bindings[f"alt-{key}"], f"workspace --auto-back-and-forth {workspace}")
            self.assertEqual(self.bindings[f"alt-shift-{key}"], f"move-node-to-workspace {workspace}")

    def test_resize_matches_i3_and_modes_have_exit(self):
        resize = self.config["mode"]["resize"]["binding"]
        self.assertEqual(resize["j"], "resize height -50")
        self.assertEqual(resize["k"], "resize height +50")
        for name, mode in self.config["mode"].items():
            if name != "main":
                self.assertIn("esc", mode["binding"])
                self.assertIn("enter", mode["binding"])

    def test_portable_path_and_no_second_bar_daemon(self):
        path = self.config["exec"]["env-vars"]["PATH"]
        self.assertIn("/usr/local/bin", path)
        self.assertIn("/opt/homebrew/bin", path)
        self.assertNotIn("/opt/homebrew/opt", str(self.config))
        self.assertNotIn("close-all-windows-but-current", str(self.config))

    def test_workspace_callback_uses_direct_fast_path(self):
        callback = " ".join(self.config["exec-on-workspace-change"])
        self.assertIn("plugins/spaces.sh", callback)
        self.assertNotIn("--trigger aerospace_workspace_change", callback)

    def test_workspace_bar_has_no_periodic_full_rebuild(self):
        setup = (PROFILE / "spaces.sh").read_text()
        self.assertIn("update_freq=0", setup)
        self.assertNotIn("front_app_switched", setup)
        self.assertNotIn("space_windows_change", setup)


class WorkspaceTests(unittest.TestCase):
    def run_update(self, focused="2", previous="1", sender="", fail=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mock = root / "aerospace"
            mock.write_text("""#!/bin/bash
if [ "$FAIL" = 1 ]; then exit 1; fi
case "$1 $2" in
  'list-workspaces --focused') echo "$FOCUSED" ;;
  'list-workspaces --all') printf '1\\n2\\n10\\nT\\n' ;;
  'list-workspaces --monitor') printf '1\\n2\\n10\\nT\\n' ;;
  'list-monitors ') echo '1 | Display' ;;
  'list-windows --all') printf '2|Terminal\\nT|Editor\\n' ;;
esac
""")
            mock.chmod(0o755)
            bar = root / "sketchybar"
            bar.write_text('#!/bin/bash\nprintf "%s\\n" "$@" >> "$BAR_LOG"\n')
            bar.chmod(0o755)
            log = root / "bar.log"
            env = {
                **os.environ,
                "PATH": f"{root}:/usr/bin:/bin",
                "BAR_LOG": str(log),
                "FOCUSED": focused,
                "FOCUSED_WORKSPACE": focused,
                "PREV_WORKSPACE": previous,
                "SENDER": sender,
                "FAIL": str(int(fail)),
            }
            result = subprocess.run(["/bin/bash", str(PROFILE / "workspaces.sh")], env=env,
                                    capture_output=True, text=True)
            return result, log.read_text() if log.exists() else ""

    def test_startup_without_event_variables_and_empty_focused_workspace(self):
        result, output = self.run_update(focused="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("space.\n", output)
        self.assertIn("space.1\n", output)
        self.assertIn("space.T\n", output)
        self.assertIn("background.drawing=on", output)
        self.assertNotIn("--add\nspace\n", output)
        self.assertIn("--add\nitem\n", output)

    def test_unavailable_aerospace_leaves_bar_unchanged(self):
        result, output = self.run_update(fail=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "")

    def test_all_workspaces_remain_clickable(self):
        result, output = self.run_update()
        self.assertEqual(result.returncode, 0)
        self.assertIn("click_script=aerospace workspace 10", output)
        self.assertIn("display=1", output)
        self.assertNotIn("display=0", output)

    def test_workspace_has_only_one_number(self):
        result, output = self.run_update()
        self.assertEqual(result.returncode, 0)
        self.assertIn("label.drawing=off", output)
        self.assertNotIn("label=1\n", output)
        self.assertIn("background.color=0xffe7894c\nbackground.drawing=off", output)

    def test_workspace_switch_only_updates_two_highlights(self):
        result, output = self.run_update(
            focused="3",
            previous="2",
            sender="aerospace_workspace_change",
            fail=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--add\n", output)
        self.assertNotIn("--remove\n", output)
        self.assertEqual(output.count("--set\n"), 2)
        self.assertIn("space.2\n", output)
        self.assertIn("space.3\n", output)


if __name__ == "__main__":
    unittest.main()
