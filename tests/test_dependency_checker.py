import unittest
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

    def test_version_detection_uses_first_nonempty_output_line(self):
        completed = Mock(stdout="\nDemo version 3.4\nadditional details\n", stderr="")
        with patch.object(checker.subprocess, "run", return_value=completed) as run:
            result = checker.get_tool_version("/tools/demo", ["--version"])
        self.assertEqual(result, "Demo version 3.4")
        run.assert_called_once()

    def test_version_subprocess_failure_is_reported(self):
        with patch.object(checker.subprocess, "run", side_effect=PermissionError("denied")):
            self.assertEqual(checker.get_tool_version("demo", []), "Version check failed")

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
