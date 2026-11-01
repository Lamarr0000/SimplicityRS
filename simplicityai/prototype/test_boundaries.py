"""Tests that unauthorized model output cannot reach a desktop tool."""
import unittest
from unittest.mock import Mock
from app import State
from desktop import BUTTONS, Calculator


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.state = State()
        self.state.calc = Mock()
        self.state.emit = Mock()

    def test_arbitrary_tool_rejected(self):
        with self.assertRaises(ValueError):
            self.state.execute({"function": {"name": "shell", "arguments": {"command": "whoami"}}})
        self.state.calc.call.assert_not_called()

    def test_extra_launch_arguments_rejected(self):
        with self.assertRaises(ValueError):
            self.state.execute({"function": {"name": "open_calculator", "arguments": {"path": "other.exe"}}})
        self.state.calc.call.assert_not_called()

    def test_stop_prevents_dispatch(self):
        self.state.cancel.set()
        with self.assertRaises(InterruptedError):
            self.state.execute({"function": {"name": "open_calculator", "arguments": {}}})
        self.state.calc.call.assert_not_called()

    def test_text_arguments_rejected(self):
        with self.assertRaises(ValueError):
            self.state.execute({"function": {"name": "open_calculator", "arguments": "{}"}})
        self.state.calc.call.assert_not_called()

    def test_allowed_call_dispatches(self):
        self.state.calc.call.return_value = {"open": True, "display": "Display is 0"}
        result = self.state.execute({"function": {"name": "open_calculator", "arguments": {}}})
        self.assertTrue(result["open"])
        self.state.calc.call.assert_called_once_with("open_calculator", {})

    def test_no_navigation_or_close_buttons(self):
        self.assertNotIn("Close", BUTTONS)
        self.assertNotIn("TogglePaneButton", BUTTONS)

    def test_unknown_button_rejected_before_uia(self):
        calc = Calculator.__new__(Calculator)
        calc._window = Mock()
        with self.assertRaises(ValueError):
            calc._press("Close", 1)
        calc._window.assert_not_called()

    def test_stale_observation_rejected_before_uia(self):
        calc = Calculator.__new__(Calculator)
        calc.version = 3
        calc._window = Mock()
        with self.assertRaises(ValueError):
            calc._press("num1Button", 2)
        calc._window.assert_not_called()

    def test_changed_display_prevents_button_press(self):
        calc = Calculator.__new__(Calculator)
        calc.version = 3
        calc.last_state = {"open": True, "display": "Display is 0"}
        calc._observe = Mock(return_value={"open": True, "display": "Display is 7"})
        calc._window = Mock()
        with self.assertRaises(ValueError):
            calc._press("num1Button", 3)
        calc._window.assert_not_called()


if __name__ == "__main__":
    unittest.main()
