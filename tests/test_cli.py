import io
import logging
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main as cli
from utils import logger as app_logger


class CliInputTests(unittest.TestCase):
    def test_empty_and_non_numeric_menu_inputs_do_not_crash(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["", "hello", "5"]), \
                patch.object(cli, "setup_logger"), \
                patch.object(cli, "log_action") as log_action, \
                patch.object(cli, "log_error") as log_error, \
                redirect_stdout(output):
            cli.main()

        self.assertEqual(output.getvalue().count("Invalid menu selection"), 2)
        self.assertTrue(any("''" in call.args[0] for call in log_error.call_args_list))
        self.assertTrue(any("'hello'" in call.args[0] for call in log_error.call_args_list))
        log_action.assert_any_call("Application exited normally.")

    def test_valid_dependency_choice_returns_to_menu(self):
        results = [{"name": "Demo", "installed": False, "version": "Not Available",
                   "path": None, "required": True}]
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "", "5"]), \
                patch.object(cli, "setup_logger"), \
                patch.object(cli, "check_all_dependencies", return_value=results) as check, \
                patch.object(cli, "print_dependency_report") as report, \
                patch.object(cli, "log_action"), patch.object(cli, "log_error"), \
                redirect_stdout(output):
            cli.main()
        check.assert_called_once()
        report.assert_called_once_with(results)
        self.assertGreaterEqual(output.getvalue().count("Main Menu"), 2)

    def test_action_and_error_logs_survive_logger_restart(self):
        action = "test persistence action 2026-11-22"
        error = "test persistence error 2026-11-22"
        app_logger.log_action(action)
        logging.shutdown()
        app_logger.setup_logger()
        app_logger.log_error(error)

        contents = app_logger.get_logs()
        self.assertIn(action, contents)
        self.assertIn(error, contents)
        self.assertIn("[INFO]", contents)
        self.assertIn("[ERROR]", contents)


if __name__ == "__main__":
    unittest.main()
