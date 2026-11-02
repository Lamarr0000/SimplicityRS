"""Desktop boundaries and evidence contract. No real input or apps launched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
import server
from desktop_tools import DesktopTools,create_text,launch_app
from tool_state import ToolState
from target_scope import TargetConversation

TREE='Focused Window: Microsoft Edge\nOpened Windows: Microsoft Edge\nUI Tree:\n (123,456) edit "Address and search bar" [action: fill]\n (33,66) button "Search" [action: click]'


class DesktopTests(unittest.TestCase):
    def state(self):
        state=ToolState();state.chat=TargetConversation();state.emit=Mock()
        return state

    def test_real_control_ids_and_freshness(self):
        desktop=DesktopTools();desktop.bridge=Mock();desktop.bridge.call.return_value=TREE
        with patch.object(desktop,'foreground',return_value=45):result=desktop.observe(lambda:None)
        self.assertEqual(result['controls'],2);self.assertEqual(desktop.elements[1],[123,456])
        with patch.object(desktop,'foreground',return_value=46):
            with self.assertRaisesRegex(ValueError,'foreground changed'):
                desktop.execute('desktop_interact',{'snapshot':result['snapshot'],'element':1,'action':'click'},lambda:None)
        self.assertEqual(desktop.bridge.call.call_count,1)

    def test_bad_ids_are_not_coordinates(self):
        desktop=DesktopTools();desktop.bridge=Mock();desktop.snapshot='abc';desktop.observed_at=__import__('time').monotonic();desktop.window=45
        with patch.object(desktop,'foreground',return_value=45):
            with self.assertRaisesRegex(ValueError,'not observed'):
                desktop.execute('desktop_interact',{'snapshot':'abc','element':999,'action':'click'},lambda:None)
        desktop.bridge.call.assert_not_called()

    def test_control_rechecked_and_token_consumed(self):
        desktop=DesktopTools();desktop.bridge=Mock();desktop.bridge.call.return_value=TREE
        with patch.object(desktop,'foreground',return_value=45):observation=desktop.observe(lambda:None)
        desktop.bridge.call.side_effect=[TREE,'clicked']
        with patch.object(desktop,'foreground',return_value=45),patch('desktop_tools.ctypes.WinDLL'),patch('psutil.Process') as process:
            process.return_value.exe.return_value='C:/Program Files/Microsoft/Edge/Application/msedge.exe'
            args={'snapshot':observation['snapshot'],'element':1,'action':'click'}
            result=desktop.execute('desktop_interact',args,lambda:None)
            self.assertFalse(result['completion_verified'])
            self.assertEqual(desktop.bridge.call.call_args.args[:2],('Click',{'loc':[123,456],'clicks':1}))
            with self.assertRaisesRegex(ValueError,'stale'):desktop.execute('desktop_interact',args,lambda:None)

    def test_recovery_input_is_blocked(self):
        desktop=DesktopTools();desktop.bridge=Mock();desktop.bridge.call.return_value=TREE
        with patch.object(desktop,'foreground',return_value=45):observation=desktop.observe(lambda:None)
        with patch.object(desktop,'foreground',return_value=45),patch('desktop_tools.ctypes.WinDLL'),patch('psutil.Process') as process:
            process.return_value.exe.return_value='C:/Recovery/DiskImageCloneApp.exe'
            with self.assertRaisesRegex(ValueError,'not enabled'):
                desktop.execute('desktop_interact',{'snapshot':observation['snapshot'],'element':1,'action':'click'},lambda:None)
        self.assertEqual(desktop.bridge.call.call_count,1)

    def test_other_machine_blocked_before_any_action(self):
        state=self.state();state.chat.target='other';state.desktop.execute=Mock()
        with self.assertRaisesRegex(ValueError,'not connected'):
            state.execute({'function':{'name':'open_desktop_app','arguments':{'app':'edge'}}})
        state.desktop.execute.assert_not_called()

    def test_schema_rejects_arbitrary_executable_and_wrong_types(self):
        state=self.state();state.desktop.execute=Mock()
        for args in [{'app':'cmd.exe'},{'app':'edge','executable':'powershell.exe'},{'app':12}]:
            with self.assertRaises(Exception):state.execute({'function':{'name':'open_desktop_app','arguments':args}})
        state.desktop.execute.assert_not_called()

    def test_file_exclusive_creation_reread_and_no_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);result=create_text('Simplicity test.txt','Hello, recovery!\n',root)
            self.assertTrue(result['content_verified']);self.assertEqual((root/'Simplicity test.txt').read_text(), 'Hello, recovery!\n')
            with self.assertRaises(FileExistsError):create_text('Simplicity test.txt','overwrite',root)
            for name in ['../bad.txt','C:\\bad.txt','con.txt','bad.txt:stream','file.txt.']:
                with self.assertRaises(ValueError):create_text(name,'bad',root)

    def test_urls_never_become_shell_or_local_files(self):
        with patch('desktop_tools.subprocess.Popen') as launch:
            for url in ['file:///C:/secret','javascript:alert(1)','https://user:pass@example.com','https://example.com/\ncmd']:
                with self.assertRaises(ValueError):launch_app('edge',url)
            launch.assert_not_called()

    def test_catalog_is_reference_not_recovery_automation(self):
        result=DesktopTools().execute('get_recovery_tool_catalog',{},lambda:None)
        self.assertEqual(len(result['lazesoft']['modules']),4)
        self.assertIn('not been validated',result['lazesoft']['validation'])

    def test_stop_prevents_action(self):
        state=self.state();state.cancel.set();state.desktop.execute=Mock()
        with self.assertRaises(InterruptedError):state.execute({'function':{'name':'desktop_observe','arguments':{}}})
        state.desktop.execute.assert_not_called()


if __name__=='__main__':unittest.main()
