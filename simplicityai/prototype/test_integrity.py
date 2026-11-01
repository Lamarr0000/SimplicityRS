import unittest
from unittest.mock import Mock, patch
from integrity import collect_integrity, integrity_report


class IntegrityTests(unittest.TestCase):
    def test_clean_summary_keeps_raw_progress_out(self):
        result = {'windows_directory': 'C:\\Windows', 'errors': [], 'checks': [
            {'exit_code': 0, 'output': 'No component store corruption detected.', 'tool': 'DISM', 'errors': ''},
            {'exit_code': 0, 'output': 'Verification 50% complete.\nWindows Resource Protection did not find any integrity violations.', 'tool': 'SFC', 'errors': ''}]}
        text = integrity_report(result)
        self.assertNotIn('50%', text)
        self.assertIn('no reason to repair', text)
        self.assertIn('Full Windows output', text)

    def test_partial_result_never_gets_all_clear(self):
        result = {'windows_directory': 'C:\\Windows', 'errors': [], 'checks': [
            {'exit_code': 0, 'output': 'No component store corruption detected.', 'tool': 'DISM', 'errors': ''}]}
        self.assertNotIn('no reason to repair', integrity_report(result))

    @patch('integrity.subprocess.run')
    @patch('integrity.is_admin', return_value=False)
    def test_no_admin_runs_nothing(self, admin, run):
        result = collect_integrity(Mock(), Mock())
        run.assert_not_called()
        self.assertEqual(result['checks'], [])
        self.assertIn('No checks ran', result['errors'][0])

    @patch('integrity.subprocess.run')
    @patch('integrity.is_admin', return_value=True)
    def test_only_fixed_verification_arguments(self, admin, run):
        run.return_value = Mock(returncode=0, stdout=b'Unrecognized localized output', stderr=b'')
        result = collect_integrity(Mock(), Mock())
        args = [call.args[0][1:] for call in run.call_args_list]
        self.assertEqual(args, [['/Online', '/Cleanup-Image', '/CheckHealth'], ['/verifyonly']])
        self.assertFalse(result['repair_requested'])
        self.assertIn('needs review', integrity_report(result))

    @patch('integrity.subprocess.run')
    @patch('integrity.is_admin', return_value=True)
    def test_stop_prevents_next_tool(self, admin, run):
        run.return_value = Mock(returncode=0, stdout=b'', stderr=b'')
        stop = Mock(side_effect=[None, InterruptedError('Stopped')])
        with self.assertRaises(InterruptedError):
            collect_integrity(Mock(), stop)
        self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
