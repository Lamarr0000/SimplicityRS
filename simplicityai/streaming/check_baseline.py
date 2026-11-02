"""Baseline boundaries: fixed collectors, literal filtering, guides and scope."""
import base64
import json
import os
import subprocess
import unittest
from unittest.mock import Mock,patch
import server
from windows_baseline import inspect_windows,AREAS
from troubleshooting import guidance,requested_checks,completed_report,diagnostic_report_issue
from evidence_context import model_evidence
from tool_state import ToolState
from target_scope import TargetConversation
from desktop_workflow import web_search_request


class BaselineTests(unittest.TestCase):
    def test_all_categories_registered(self):
        tool=next(tool for tool in server.TOOLS if tool['function']['name']=='inspect_windows')
        self.assertEqual(set(tool['function']['parameters']['properties']['area']['enum']),set(AREAS))

    def test_query_is_data_not_executable_powershell(self):
        query="'; Stop-Computer; '"
        process=Mock();process.communicate.return_value=(b'{"sections":[],"changes_made":false}',b'');process.returncode=0;process.poll.return_value=0
        with patch('windows_baseline.subprocess.Popen',return_value=process) as launch:
            inspect_windows('drivers',query,lambda:None)
        args=launch.call_args.args[0];decoded=base64.b64decode(args[-1]).decode('utf-16le')
        self.assertNotIn(query,decoded);self.assertEqual(launch.call_args.kwargs['env']['SIMPLICITY_INSPECT_QUERY'],query)
        self.assertNotIn('PSModulePath',launch.call_args.kwargs['env'])
        self.assertNotIn('-ExecutionPolicy',args)

    def test_unknown_area_and_cancellation_do_not_start_a_process(self):
        with patch('windows_baseline.subprocess.Popen') as launch:
            with self.assertRaises(ValueError):inspect_windows('repair','',lambda:None)
            with self.assertRaises(InterruptedError):inspect_windows('storage','',Mock(side_effect=InterruptedError))
            launch.assert_not_called()

    def test_cancellation_terminates_owned_collector(self):
        process=Mock();process.communicate.side_effect=[subprocess.TimeoutExpired('collector',.1),(b'',b'')];process.poll.return_value=None
        check=Mock(side_effect=[None,None,InterruptedError])
        with patch('windows_baseline.subprocess.Popen',return_value=process):
            with self.assertRaises(InterruptedError):inspect_windows('storage','',check)
        process.terminate.assert_called_once()

    def test_other_windows_is_blocked_before_collecting(self):
        state=ToolState();state.chat=TargetConversation();state.chat.target='other';state.emit=Mock()
        with patch('tool_state.inspect_windows') as collect:
            with self.assertRaisesRegex(ValueError,'not connected'):state.execute({'function':{'name':'inspect_windows','arguments':{'area':'storage'}}})
            collect.assert_not_called()

    def test_guides_choose_checks_not_diagnoses(self):
        self.assertIn('inspect_windows(drivers',guidance('My USB driver is missing'))
        self.assertIn('not disk failure',guidance('The drive is running out of space'))
        self.assertIn('Boot-file corruption cannot be inferred',guidance('Windows boot files might be corrupt'))
        self.assertIn('unknown',guidance(''))

    def test_explicit_requests_route_without_unrelated_driver_storage_match(self):
        self.assertEqual(requested_checks('Inspect my wireless driver.'),{'devices','drivers'})
        self.assertEqual(requested_checks('Explain what a driver is.'),set())
        self.assertEqual(requested_checks('Do not inspect my drivers.'),set())
        self.assertEqual(requested_checks('Review recent restart error events.'),{'events'})
        self.assertEqual(requested_checks('My computer is running out of space.'),{'storage'})
        self.assertEqual(requested_checks('What is storage space?'),set())

    def test_completed_report_does_not_promise_unrun_checks(self):
        self.assertEqual(completed_report('Boot configuration is unknown. Let me check the system files next.'),'Boot configuration is unknown.')
        self.assertIsNotNone(diagnostic_report_issue('There is one update available.',{'updates'}))
        self.assertIsNone(diagnostic_report_issue('Update availability was not checked.',{'updates'}))

    def test_model_excerpt_preserves_original_and_marks_omissions(self):
        result={'sections':[{'name':'events','returned_count':20,'data':[{'Message':'x'*300} for _ in range(20)]}]}
        excerpt=json.loads(model_evidence(result,1200));section=excerpt['sections'][0]
        self.assertLess(len(section['data']),20);self.assertTrue(section['model_context_truncated'])
        self.assertEqual(len(result['sections'][0]['data']),20)

    def test_windows_viewers_use_only_fixed_launch_arguments(self):
        from desktop_tools import launch_app
        with patch('desktop_tools.subprocess.Popen') as launch:
            launch_app('device_manager')
            self.assertEqual(launch.call_args.args[0][-1],'devmgmt.msc')
            self.assertFalse(launch.call_args.kwargs['shell'])
            with self.assertRaises(ValueError):launch_app('device_manager','https://example.com')

    def test_web_search_encodes_query_as_url_data(self):
        from desktop_tools import DesktopTools
        from urllib.parse import urlsplit,parse_qs
        query='computer speed & storage test'
        with patch('desktop_tools.launch_app',return_value={'launch_requested':True}) as launch:
            DesktopTools().execute('search_web',{'query':query},lambda:None)
        app,url=launch.call_args.args
        self.assertEqual(app,'edge');self.assertEqual(parse_qs(urlsplit(url).query)['q'],[query])

    def test_search_workflow_routes_explicit_request_not_negation(self):
        self.assertEqual(web_search_request('Can you open a browser and search for speed tests googal search please'),'speed tests')
        self.assertEqual(web_search_request('Search Google for computer speed tests.'),'computer speed tests')
        self.assertIsNone(web_search_request('Do not search for computer speed tests.'))
        self.assertIsNone(web_search_request('What is a search engine?'))


if __name__=='__main__':unittest.main()
