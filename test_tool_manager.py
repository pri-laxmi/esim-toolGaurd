import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from core import dependency_checker, tool_manager


class DependencyDetectionTests(unittest.TestCase):
    def test_finds_executable_in_custom_bin_directory(self):
        install_dir = Path("C:/custom/tools")
        executable = install_dir / "bin" / "sample-tool.exe"
        with patch.object(dependency_checker.shutil, "which", return_value=None), \
                patch.object(Path, "is_file", return_value=True):
            found = dependency_checker.find_executable({
                "executable": executable.name,
                "install_dir": str(install_dir),
            })
        self.assertEqual(found, str(executable.resolve()))

    def test_finds_executable_in_install_root(self):
        install_dir = Path("C:/custom/tools")
        executable = install_dir / "sample-tool.exe"
        with patch.object(dependency_checker.shutil, "which", return_value=None), \
                patch.object(Path, "is_file", side_effect=[False, True]):
            found = dependency_checker.find_executable({
                "executable": executable.name,
                "install_dir": str(install_dir),
            })
        self.assertEqual(found, str(executable.resolve()))


class ToolManagerTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            {"name": "InstalledTool", "installed": True, "version": "1.2.3",
             "path": "C:/tools/installed.exe", "required": True},
            {"name": "MissingTool", "installed": False, "version": "Not Available",
             "path": None, "required": True},
        ]

    def test_get_installed_tools_filters_missing_tools(self):
        with patch.object(tool_manager, "check_all_dependencies", return_value=self.results):
            self.assertEqual(tool_manager.get_installed_tools(), [self.results[0]])

    def test_display_includes_status_version_path_and_statistics(self):
        output = io.StringIO()
        with patch.object(tool_manager, "check_all_dependencies", return_value=self.results):
            with redirect_stdout(output):
                tool_manager.display_installed_tools()

        report = output.getvalue()
        for expected in (
            "InstalledTool", "Status: Installed", "1.2.3", "C:/tools/installed.exe",
            "MissingTool", "Status: Missing", "Total Configured Tools : 2",
            "Compatible Tools       : 1", "Missing Tools          : 1",
        ):
            self.assertIn(expected, report)


if __name__ == "__main__":
    unittest.main()
