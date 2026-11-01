"""Browser boundary checks; no browser or desktop window is opened."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock,patch

import server  # Initialize the existing host dependency paths.
import browser_tools
from server_job import guard_server
from tool_state import ToolState
from tool_state import capability_reply
from target_scope import TargetConversation
import psutil


class BrowserTests(unittest.TestCase):
    def test_tool_identity_questions_use_app_facts_not_install_prompts(self):
        self.assertIn('already connected',capability_reply("You're probably going to need some tools like them hands."))
        self.assertIn('already connected',capability_reply('What is ThemHands?'))
        self.assertIsNone(capability_reply('Use ThemHands to open a browser.'))
        self.assertIsNone(capability_reply('Can you open a browser for me?'))

    def state(self):
        state=ToolState();state.mode='chat';state.chat=TargetConversation();state.emit=lambda *a,**kw:None
        return state

    def test_capabilities_are_local_and_explicit(self):
        state=self.state()
        with patch.object(browser_tools,'Windows',side_effect=AssertionError('No window access')):
            result=state.execute({'function':{'name':'get_tool_capabilities','arguments':{}}})
        self.assertEqual(result['name'],'ThemHands');self.assertTrue(result['browser_launch_is_not_internet_test'])

    def test_model_cannot_supply_a_url_or_executable(self):
        for args in [{'url':'file:///C:/secret'},{'path':'cmd.exe'},'not an object']:
            with patch('tool_state.open_browser') as launch:
                with self.assertRaises(ValueError):self.state().execute({'function':{'name':'open_browser_window','arguments':args}})
                launch.assert_not_called()

    def test_outside_target_is_blocked_before_browser(self):
        for text in ['Open the browser on the host outside this VM.',
                     'Open the browser on another PC.', 'Open a browser in a different VM.']:
            with self.subTest(text=text):
                state=self.state();state.chat.begin(text)
                with patch('tool_state.open_browser') as launch:
                    with self.assertRaises(ValueError):state.execute({'function':{'name':'open_browser_window','arguments':{}}})
                    launch.assert_not_called()

    def test_new_window_evidence_does_not_claim_web_or_foreground(self):
        windows=Mock();windows.matching.side_effect=[[11],[11,22]];windows.foreground.return_value=False
        with patch.object(browser_tools,'edge_path',return_value=Path('C:/Program Files/Edge/msedge.exe')), \
             patch.object(browser_tools,'Windows',return_value=windows),patch.object(browser_tools,'launch'):
            result=browser_tools.open_browser(lambda:None,lambda *a:None)
        self.assertTrue(result['new_window_observed']);self.assertFalse(result['foreground_verified'])
        self.assertFalse(result['internet_tested'])

    def test_existing_window_is_not_reported_as_new_launch(self):
        windows=Mock();windows.matching.return_value=[11]
        with patch.object(browser_tools,'edge_path',return_value=Path('C:/Edge/msedge.exe')), \
             patch.object(browser_tools,'Windows',return_value=windows),patch.object(browser_tools,'launch'):
            result=browser_tools.open_browser(lambda:None,lambda *a:None,timeout=0)
        self.assertFalse(result['ok']);self.assertFalse(result['new_window_observed'])

    def test_cancel_prevents_launch(self):
        def cancel():raise InterruptedError('cancelled')
        with patch.object(browser_tools,'edge_path',return_value=Path('C:/Edge/msedge.exe')),patch.object(browser_tools,'launch') as launch:
            with self.assertRaises(InterruptedError):browser_tools.open_browser(cancel,lambda *a:None)
            launch.assert_not_called()

    def test_blank_window_report_never_describes_a_failed_page_load(self):
        report=browser_tools.browser_report({'ok':True,'new_window_observed':True,'foreground_verified':False})
        self.assertIn('website loading has not been tested',report.lower())
        self.assertNotIn('failed to load',report.lower())
        self.assertIn('taskbar',report)

    def test_server_exit_kills_workers_but_preserves_explicit_external_app(self):
        # Real Windows job integration with harmless sleeping Python children.
        code="""import sys,subprocess,json
sys.stdin.readline()
a=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW)
b=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_BREAKAWAY_FROM_JOB)
print(json.dumps([a.pid,b.pid]),flush=True)
sys.stdin.readline()
"""
        helper=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        guard=None;external=None
        try:
            guard=guard_server(helper);helper.stdin.write(b'go\n');helper.stdin.flush()
            line=helper.stdout.readline()
            if not line:raise AssertionError(helper.stderr.read().decode())
            normal_pid,external_pid=json.loads(line);normal=psutil.Process(normal_pid);external=psutil.Process(external_pid)
            guard();guard=None;helper.wait(timeout=5);normal.wait(timeout=5)
            self.assertTrue(external.is_running())
        finally:
            if guard:guard()
            if helper.poll() is None:helper.terminate();helper.wait(timeout=5)
            if external and external.is_running():external.terminate();external.wait(timeout=5)
            for stream in (helper.stdin,helper.stdout,helper.stderr):stream.close()


if __name__=='__main__':unittest.main()
