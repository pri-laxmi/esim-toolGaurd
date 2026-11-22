import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from core import dependency_checker as checker


class DependencyCheckerTests(unittest.TestCase):
    def test_detects_installed_tool_and_version(self):
        tool = {"name": "Demo", "executable": "demo.exe", "version_args": ["--version"]}
        with patch.object(checker, "find_executable", return_value="/tools/demo.exe"), \
                patch.object(checker, "get_tool_version", return_value="Demo 2.1"):
            result = checker.check_tool(tool)
        self.assertTrue(result["installed"])
        self.assertEqual(result["version"], "Demo 2.1")
        self.assertEqual(result["path"], "/tools/demo.exe")

    def test_reports_missing_tool(self):
        with patch.object(checker, "find_executable", return_value=None):
            result = checker.check_tool({"name": "Missing", "executable": "missing.exe"})
        self.assertFalse(result["installed"])
        self.assertIsNone(result["path"])

    def test_invalid_executable_name_is_missing_not_exception(self):
        with patch.object(checker.shutil, "which", side_effect=ValueError("invalid name")):
            self.assertIsNone(checker.find_executable({"executable": "\0bad"}))
            self.assertIsNone(checker.find_executable({"executable": ""}))

    def test_finds_executable_under_registry_install_location(self):
        install_dir = Path("C:/Users/test/AppData/Local/Programs/KiCad/10.0")
        executable = install_dir / "bin" / "kicad-cli.exe"
        tool = {"name": "KiCad", "executable": "kicad-cli.exe",
                "registry_display_name": "KiCad"}
        with patch.object(checker.shutil, "which", return_value=None), \
                patch.object(checker, "_registry_install_dirs", return_value=[install_dir]), \
                patch.object(Path, "is_file", return_value=True):
            found = checker.find_executable(tool)
        self.assertEqual(found, str(executable.resolve()))

    def test_finds_executable_under_versioned_search_root(self):
        root = Path("C:/Program Files/KiCad")
        version_dir = root / "10.0"
        executable = version_dir / "bin" / "kicad-cli.exe"
        tool = {"name": "KiCad", "executable": "kicad-cli.exe",
                "install_search_roots": [str(root)]}
        with patch.object(checker.shutil, "which", return_value=None), \
                patch.object(checker, "_registry_install_dirs", return_value=[]), \
                patch.object(Path, "iterdir", return_value=[version_dir]), \
                patch.object(Path, "is_dir", return_value=True), \
                patch.object(Path, "is_file", side_effect=[False, False, True]):
            found = checker.find_executable(tool)
        self.assertEqual(found, str(executable.resolve()))

    def test_version_detection_uses_first_nonempty_output_line(self):
        completed = Mock(returncode=0, stdout="\nDemo version 3.4\nadditional details\n", stderr="")
        with patch.object(checker.subprocess, "run", return_value=completed) as run:
            result = checker.get_tool_version("/tools/demo", ["--version"])
        self.assertEqual(result, "Demo version 3.4")
        run.assert_called_once()

    def test_version_subprocess_failure_is_reported(self):
        with patch.object(checker.subprocess, "run", side_effect=PermissionError("denied")):
            self.assertEqual(checker.get_tool_version("demo", []), "Version check failed")

    def test_nonzero_version_command_is_failure_even_with_output(self):
        completed = Mock(returncode=1, stdout="Demo 2.1", stderr="error")
        with patch.object(checker.subprocess, "run", return_value=completed):
            self.assertEqual(checker.get_tool_version("demo", []), "Version check failed")

    def test_executable_is_not_installed_when_version_check_fails(self):
        tool = {"name": "Demo", "executable": "demo", "version_args": ["--version"],
                "version_requirement": {"minimum": "2.0"}}
        with patch.object(checker, "find_executable", return_value="/tools/demo"), \
                patch.object(checker, "get_tool_version", return_value="Version check failed"):
            result = checker.check_tool(tool)
        self.assertTrue(result["detected"])
        self.assertFalse(result["installed"])
        self.assertEqual(result["status"], "Version check failed")
        self.assertEqual(result["path"], "/tools/demo")

    def test_registered_version_verifies_windows_install(self):
        tool = {"name": "KiCad", "executable": "kicad-cli.exe",
                "version_requirement": {"minimum": "7.0"},
                "registry_display_name": "KiCad"}
        with patch.object(checker, "find_executable", return_value="C:/KiCad/bin/kicad-cli.exe"), \
                patch.object(checker, "get_tool_version") as get_version, \
                patch.object(checker, "_registry_version_for_executable", return_value="10.0.8"):
            result = checker.check_tool(tool)
        get_version.assert_not_called()
        self.assertTrue(result["installed"])
        self.assertEqual(result["version"], "10.0.8")
        self.assertEqual(result["version_source"], "registry")

    def test_version_requirement_accepts_minimum_and_rejects_old_version(self):
        tool = {"name": "Demo", "executable": "demo", "version_args": ["--version"],
                "version_pattern": r"Demo\s+(\d+(?:\.\d+)+)",
                "version_requirement": {"minimum": "2.0"}}
        with patch.object(checker, "find_executable", return_value="/tools/demo"), \
                patch.object(checker, "get_tool_version", return_value="2.1.0"):
            compatible = checker.check_tool(tool)
        self.assertTrue(compatible["installed"])
        self.assertTrue(compatible["compatible"])

        with patch.object(checker, "find_executable", return_value="/tools/demo"), \
                patch.object(checker, "get_tool_version", return_value="1.9.9"):
            incompatible = checker.check_tool(tool)
        self.assertTrue(incompatible["detected"])
        self.assertFalse(incompatible["installed"])
        self.assertEqual(incompatible["status"], "Incompatible version")

    def test_ngspice_pattern_extracts_version_from_banner(self):
        tool = checker.load_dependencies()[0]
        banner = Mock(
            returncode=0,
            stdout="******\n** ngspice-47 : Circuit level simulation program",
            stderr="",
        )
        with patch.object(checker.subprocess, "run", return_value=banner):
            version = checker.get_tool_version(
                "ngspice.exe", ["-v"], tool["version_pattern"]
            )
        self.assertEqual(version, "47")

    def test_missing_and_invalid_configuration(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                checker.load_dependencies()
        with patch("builtins.open", mock_open(read_data="{")):
            with self.assertRaises(ValueError):
                checker.load_dependencies()
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                checker.load_dependencies()


if __name__ == "__main__":
    unittest.main()
