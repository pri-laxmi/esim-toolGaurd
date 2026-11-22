import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from core import installer
from main import _install_a_tool


class InstallerTests(unittest.TestCase):
    def test_ngspice_swap_activates_staged_install_and_returns_backup(self):
        staged = Path("C:/tools/.staged/ngspice")
        install_dir = Path("C:/tools/ngspice")
        backup = Path("C:/tools/ngspice.backup-test")
        with patch.object(installer.uuid, "uuid4", return_value=SimpleNamespace(hex="test")), \
                patch.object(Path, "exists", return_value=True), \
                patch.object(Path, "rename", autospec=True) as rename:
            result = installer._swap_install_directory(staged, install_dir)

        self.assertEqual(result, backup)
        self.assertEqual(rename.call_args_list, [
            call(install_dir, backup),
            call(staged, install_dir),
        ])

    def test_ngspice_swap_restores_old_install_if_activation_fails(self):
        staged = Path("C:/tools/.staged/ngspice")
        install_dir = Path("C:/tools/ngspice")
        backup = Path("C:/tools/ngspice.backup-test")

        def rename(source, destination):
            if source == staged:
                raise OSError("activation failed")
            return destination

        with patch.object(installer.uuid, "uuid4", return_value=SimpleNamespace(hex="test")), \
                patch.object(Path, "exists", side_effect=[True, False]), \
                patch.object(Path, "rename", autospec=True, side_effect=rename) as rename_mock:
            with self.assertRaisesRegex(OSError, "activation failed"):
                installer._swap_install_directory(staged, install_dir)

        self.assertEqual(rename_mock.call_args_list, [
            call(install_dir, backup),
            call(staged, install_dir),
            call(backup, install_dir),
        ])

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
