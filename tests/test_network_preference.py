"""No real services, routes, privileges, or authentication are exercised."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "network_preference",
    Path(__file__).resolve().parents[1] / "system/eww-network-preference.py",
)
assert spec and spec.loader
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(helper, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.trust_patch = patch.object(helper, "trusted")
        self.trust_patch.start()
        self.addCleanup(self.trust_patch.stop)
        self.file = self.root / "20-wlan.network"
        self.file.write_text("[Match]\nName=wl*\n[Network]\nDHCP=yes\n")
        self.link = {
            "Name": "wlan0",
            "NetworkFile": str(self.file),
            "NetworkFileDropins": [],
            "Index": 4,
            "eligible": True,
            "OperationalState": "routable",
        }

    def test_simple_dhcp_target(self):
        self.assertEqual(
            helper.destination(self.link), Path(str(self.file) + ".d") / helper.DROPIN
        )

    def test_invalid_interface(self):
        for name in ["../../etc", "-x", "wlan0;id", "a" * 16]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                helper.destination({**self.link, "Name": name})

    def test_external_config_path(self):
        with self.assertRaises(ValueError):
            helper.destination({**self.link, "NetworkFile": "/tmp/evil.network"})

    def test_static_routing_rejected(self):
        for extra in ["[Route]\nGateway=1.2.3.4\n", "[RoutingPolicyRule]\nTable=200\n"]:
            self.file.write_text("[Network]\nDHCP=yes\n" + extra)
            with self.assertRaises(ValueError):
                helper.destination(self.link)

    def test_non_dhcp_rejected(self):
        self.file.write_text("[Network]\nAddress=192.0.2.2/24\n")
        with self.assertRaises(ValueError):
            helper.destination(self.link)

    def test_other_dropin_rejected(self):
        with self.assertRaises(ValueError):
            helper.destination(
                {
                    **self.link,
                    "NetworkFileDropins": ["/usr/lib/systemd/network/foo.conf"],
                }
            )

    def test_unrecognized_override_rejected(self):
        target = helper.destination(self.link)
        target.parent.mkdir()
        target.write_text("unrelated configuration")
        with self.assertRaises(ValueError):
            helper.destination(self.link)

    def test_owned_override_accepted(self):
        target = helper.destination(self.link)
        target.parent.mkdir()
        target.write_text(helper.content(50))
        self.assertEqual(helper.destination(self.link), target)

    def test_unprivileged_mutation_rejected(self):
        with (
            patch.object(helper.os, "geteuid", return_value=1000),
            self.assertRaises(PermissionError),
        ):
            helper.apply("wlan0")

    def test_inspect_never_mutates(self):
        link = {**self.link, "Type": "wlan", "metric": 600, "reason": ""}
        with (
            patch.object(helper, "discover", return_value=[link]),
            patch.object(helper, "replace") as mutate,
        ):
            result = helper.snapshot()
            self.assertFalse(result["available"])
            self.assertEqual(result["interfaces"][0]["index"], 4)
            mutate.assert_not_called()

    def test_reset_available_with_one_interface(self):
        target = helper.destination(self.link)
        target.parent.mkdir()
        target.write_text(helper.content(50))
        link = {**self.link, "Type": "wlan", "metric": 100, "reason": ""}
        with patch.object(helper, "discover", return_value=[link]):
            result = helper.snapshot()
            self.assertFalse(result["available"])
            self.assertTrue(result["reset_available"])
            self.assertTrue(result["interfaces"][0]["preferred"])

    def test_reset_removes_disconnected_owned_profile(self):
        target = helper.destination(self.link)
        target.parent.mkdir()
        target.write_text(helper.content(50))
        real_path = Path

        def paths(value):
            return (
                self.root / "run"
                if value == "/run/eww-network-preference"
                else real_path(value)
            )

        with (
            patch.object(helper, "Path", side_effect=paths),
            patch.object(helper.os, "geteuid", return_value=0),
            patch.object(helper, "discover", return_value=[]),
            patch.object(helper, "run") as commands,
        ):
            helper.apply(None)
            self.assertFalse(target.exists())
            commands.assert_called_once_with(
                "/usr/bin/networkctl", "--no-reconfigure", "reload"
            )

    def test_shared_network_profile_rejected(self):
        one = {**self.link, "Type": "wlan", "AdministrativeState": "configured"}
        two = {**one, "Name": "wlan1", "Index": 5}
        with (
            patch.object(
                helper,
                "run",
                side_effect=[
                    json.dumps({"Interfaces": [one, two]}),
                    json.dumps(one),
                    json.dumps(two),
                ],
            ),
            patch.object(Path, "exists", return_value=True),
            patch.object(helper, "destination"),
        ):
            links = helper.discover()
            self.assertTrue(all(not link["eligible"] for link in links))
            self.assertIn("shared", links[0]["reason"])

    def rollback(self, failure):
        second = {**self.link, "Name": "enp1s0", "Index": 2}
        first_target = self.root / "first.conf"
        second_target = self.root / "second.conf"
        first_target.write_text(helper.content(600))

        def target(link):
            return first_target if link["Name"] == "wlan0" else second_target

        # Redirect only the fixed runtime lock directory into the test fixture.
        real_path = Path

        def paths(value):
            return (
                self.root / "run"
                if value == "/run/eww-network-preference"
                else real_path(value)
            )

        with (
            patch.object(helper, "Path", side_effect=paths),
            patch.object(helper.os, "geteuid", return_value=0),
            patch.object(helper, "discover", return_value=[self.link, second]),
            patch.object(helper, "destination", side_effect=target),
            patch.object(
                helper,
                "run",
                side_effect=[None, failure, None, None],
            ) as commands,
        ):
            with self.assertRaisesRegex(RuntimeError, "previous settings restored"):
                helper.apply("wlan0")
            self.assertEqual(first_target.read_text(), helper.content(600))
            self.assertFalse(second_target.exists())
            self.assertEqual(commands.call_count, 4)
            self.assertTrue(
                all(
                    call.args[0] == "/usr/bin/networkctl"
                    for call in commands.call_args_list
                )
            )

    def test_transaction_rollback(self):
        self.rollback(RuntimeError("apply failed"))

    def test_sigterm_handler_enters_rollback(self):
        try:
            helper.cancelled(15, None)
        except RuntimeError as error:
            self.rollback(error)
        else:
            self.fail("SIGTERM must raise a recoverable exception")

    def test_trust_rejects_user_owned_path(self):
        self.trust_patch.stop()
        # Test fixture is user-owned, never an allowed privileged target.
        with self.assertRaises(ValueError):
            helper.trusted(self.file)

    def test_trust_rejects_symlink(self):
        self.trust_patch.stop()
        symlink = self.root / "symlink.network"
        symlink.symlink_to(self.file)
        with self.assertRaises(ValueError):
            helper.trusted(symlink)


if __name__ == "__main__":
    unittest.main()
