import unittest
import io
import json
from unittest.mock import Mock, patch
from app import State
from health import screening


class HealthChecks(unittest.TestCase):
    def test_equals_forces_independent_reread(self):
        state = State()
        state.calc = Mock()
        state.emit = Mock()
        state.calc.call.side_effect = [{'display': '96'}, {'display': '96', 'observation': 9}]
        result = state.execute({'function': {'name': 'press_calculator_button',
                               'arguments': {'button_id': 'equalButton', 'observation': 7}}})
        self.assertEqual(state.calc.call.call_args_list[-1].args, ('observe_calculator', {}))
        self.assertTrue(result['final_display_reread'])
        self.assertEqual(result['display'], '96')

    def test_failed_final_reread_cannot_return_verified_result(self):
        state = State()
        state.calc = Mock()
        state.emit = Mock()
        state.calc.call.side_effect = [{'display': '96'}, RuntimeError('Window unavailable')]
        with self.assertRaisesRegex(RuntimeError, 'Window unavailable'):
            state.execute({'function': {'name': 'press_calculator_button',
                           'arguments': {'button_id': 'equalButton', 'observation': 7}}})

    def test_numeric_draft_is_withheld_then_rewritten(self):
        state = State()
        state.mode = 'health'
        state.health_snapshot = {'schema': 1}
        state.ensure_runtime = Mock()
        state.emit = Mock()
        state.ask = Mock(side_effect=[{'role': 'assistant', 'content': '5 errors for IDs 1801 and 1803'},
                                     {'role': 'assistant', 'content': 'Current security status is unknown. What symptoms have you noticed?'}])
        state.run('Review')
        published = [call.args[1] for call in state.emit.call_args_list if call.args[0] == 'assistant_chunk']
        self.assertEqual(published, ['Current security status is unknown. What symptoms have you noticed?'])

    def test_repeated_numeric_claim_never_finishes(self):
        state = State()
        state.mode = 'health'
        state.health_snapshot = {'schema': 1}
        state.ensure_runtime = Mock()
        state.emit = Mock()
        state.ask = Mock(return_value={'role': 'assistant', 'content': '5 events'})
        state.run('Review')
        self.assertFalse(any(c.args[0] == 'assistant_chunk' for c in state.emit.call_args_list))
        self.assertFalse(any(c.args[0] == 'status' and c.args[1].startswith('Finished') for c in state.emit.call_args_list))

    def test_missing_data_is_not_a_clean_bill_of_health(self):
        snapshot = {"memory": None, "volumes": [], "system_events": None,
                    "collection_errors": ["Memory unavailable"]}
        self.assertEqual(screening(snapshot), [])
        self.assertEqual(snapshot["collection_errors"], ["Memory unavailable"])

    def test_percentage_headroom_flag_with_plenty_of_bytes(self):
        flags = screening({"volumes": [{"drive": "D:", "free_gib": 120, "free_percent": 6.5}]})
        self.assertEqual(len(flags), 1)
        self.assertIn("120 GiB", flags[0]["evidence"])
        self.assertNotIn("failure", flags[0]["finding"])

    def test_absolute_low_space_also_flagged(self):
        flags = screening({"volumes": [{"drive": "X:", "free_gib": 5, "free_percent": 50}]})
        self.assertEqual(len(flags), 1)

    def test_low_memory_flagged(self):
        flags = screening({"memory": {"available_gib": 1, "available_percent": 25}})
        self.assertEqual(flags[0]["area"], "Memory")

    def test_sampled_events_not_called_hardware_failure(self):
        flags = screening({"system_events": {"sampled_count": 300, "window_days": 7}})
        self.assertIn("300 sampled", flags[0]["evidence"])
        self.assertIn("do not prove", flags[0]["next_check"])

    def test_health_mode_cannot_launch_apps(self):
        state = State()
        state.mode = "health"
        state.calc = Mock()
        with self.assertRaises(ValueError):
            state.execute({"function": {"name": "open_calculator", "arguments": {}}})
        state.calc.call.assert_not_called()

    @patch("app.collect_health")
    def test_health_tool_never_accepts_a_command(self, collect):
        state = State()
        state.mode = "health"
        with self.assertRaises(ValueError):
            state.execute({"function": {"name": "get_health_snapshot", "arguments": {"command": "anything"}}})
        collect.assert_not_called()

    @patch("app.collect_health", return_value={"schema": 1, "collection_errors": []})
    def test_snapshot_cached_and_no_desktop_initialized(self, collect):
        state = State()
        state.mode = "health"
        state.emit = Mock()
        call = {"function": {"name": "get_health_snapshot", "arguments": {}}}
        state.execute(call)
        state.execute(call)
        collect.assert_called_once_with()
        self.assertIsNone(state.calc)

    @patch("app.urllib.request.urlopen")
    def test_truncated_explanation_is_not_marked_complete(self, urlopen):
        urlopen.return_value = io.BytesIO((json.dumps({"message": {"content": "Partial"},
                                          "done": True, "done_reason": "length"}) + "\n").encode())
        state = State()
        state.mode = "health"
        state.emit = Mock()
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            state.ask()


if __name__ == "__main__":
    unittest.main()
