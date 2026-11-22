import unittest
from unittest.mock import Mock, patch

from core import installer
from main import _install_a_tool


class InstallerTests(unittest.TestCase):
    def test_valid_package_id_runs_winget_command(self):
        completed = Mock(returncode=0, stdout="installed", stderr="")
        with patch.object(installer, "check_winget", return_value=True), \
                patch.object(installer.subprocess, "run", return_value=completed) as run:
            result = installer.install_with_winget("Vendor.Tool_2")
        self.assertTrue(result["success"])
        self.assertIn("--id", run.call_args.args[0])
        self.assertIn("Vendor.Tool_2", run.call_args.args[0])

    def test_invalid_package_id_is_rejected_without_running_command(self):
        with patch.object(installer.subprocess, "run") as run:
            result = installer.install_with_winget("bad id; command")
        self.assertFalse(result["success"])
        self.assertIn("Invalid", result["message"])
        run.assert_not_called()

    def test_missing_winget_is_reported(self):
        with patch.object(installer, "check_winget", return_value=False):
            result = installer.install_with_winget("Vendor.Tool")
        self.assertFalse(result["success"])
        self.assertIn("winget", result["message"])

    def test_winget_failure_and_os_error_are_reported(self):
        failed = Mock(returncode=1, stdout="", stderr="package unavailable")
        with patch.object(installer, "check_winget", return_value=True), \
                patch.object(installer.subprocess, "run", return_value=failed):
            result = installer.install_with_winget("Vendor.Tool")
        self.assertFalse(result["success"])
        self.assertIn("package unavailable", result["message"])

        with patch.object(installer, "check_winget", return_value=True), \
                patch.object(installer.subprocess, "run", side_effect=PermissionError("denied")):
            result = installer.install_with_winget("Vendor.Tool")
        self.assertFalse(result["success"])
        self.assertIn("denied", result["message"])

    def test_user_cancellation_does_not_call_installer(self):
        tool = {"name": "Demo", "executable": "demo.exe", "installer": "winget",
                "package_id": "Vendor.Demo"}
        missing = [{"name": "Demo", "installed": False}]
        with patch("main.load_dependencies", return_value=[tool]), \
                patch("main.check_all_dependencies", return_value=missing), \
                patch("builtins.input", side_effect=["1", "n"]), \
                patch("main.install_tool") as install:
            _install_a_tool()
        install.assert_not_called()

    def test_invalid_tool_selection_does_not_call_installer(self):
        tool = {"name": "Demo", "executable": "demo.exe", "installer": "winget",
                "package_id": "Vendor.Demo"}
        missing = [{"name": "Demo", "installed": False}]
        for selection in ("abc", "9"):
            with self.subTest(selection=selection), \
                    patch("main.load_dependencies", return_value=[tool]), \
                    patch("main.check_all_dependencies", return_value=missing), \
                    patch("builtins.input", return_value=selection), \
                    patch("main.install_tool") as install:
                _install_a_tool()
                install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
