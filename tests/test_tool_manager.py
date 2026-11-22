import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from core import tool_manager


class ToolManagerTests(unittest.TestCase):
    def setUp(self):
        self.tools = [
            {"name": "Installed", "installed": True, "version": "1.4.0",
             "path": "C:/tools/installed.exe", "required": True},
            {"name": "Missing", "installed": False, "version": "Not Available",
             "path": None, "required": True},
        ]

    def test_get_installed_tools_only_returns_detected_tools(self):
        with patch.object(tool_manager, "check_all_dependencies", return_value=self.tools):
            self.assertEqual(tool_manager.get_installed_tools(), [self.tools[0]])

    def test_display_shows_installed_name_version_path_and_counts(self):
        output = io.StringIO()
        with patch.object(tool_manager, "check_all_dependencies", return_value=self.tools):
            with redirect_stdout(output):
                result = tool_manager.display_installed_tools()
        report = output.getvalue()
        for expected in (
            "Installed", "1.4.0", "C:/tools/installed.exe", "Missing",
            "Total Configured Tools : 2", "Successfully Detected  : 1",
            "Missing Tools          : 1",
        ):
            self.assertIn(expected, report)
        self.assertEqual(result, self.tools)


if __name__ == "__main__":
    unittest.main()
