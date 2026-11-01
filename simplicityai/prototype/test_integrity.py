import unittest
from unittest.mock import Mock, patch
from integrity import collect_integrity, integrity_report


class IntegrityTests(unittest.TestCase):
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
