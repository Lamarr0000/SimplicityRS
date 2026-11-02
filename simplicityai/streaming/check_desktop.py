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
from desktop_workflow import desktop_request,unfinished_draft,search_result_observed

TREE='Focused Window: Microsoft Edge\nOpened Windows: Microsoft Edge\nUI Tree:\n (123,456) edit "Address and search bar" [action: fill]\n (33,66) button "Search" [action: click]'


class DesktopTests(unittest.TestCase):
    def test_authorized_work_does_not_end_with_permission_or_promises(self):
        self.assertTrue(desktop_request('HEY CAN YOU OPEN UP A WET BROWSER AND NAVIGATE THE GOOGEL'))
        for text in ['Would you like me to proceed?','Let me proceed.',"I'll type the search query.",'Could you tell me where the search box is located?']:
            self.assertTrue(unfinished_draft(text),text)
        self.assertFalse(unfinished_draft('Google shows search results for computer speed test.'))
        self.assertFalse(unfinished_draft('The tool failed: the search field was not accessible.'))
        self.assertFalse(desktop_request('Explain the difference between RAM and storage.'))

    def test_search_requires_observed_destination(self):
        self.assertFalse(search_result_observed('Google homepage is ready: https://www.google.com/'))
        self.assertTrue(search_result_observed('Address: https://www.google.com/search?q=computer+speed+test'))
        self.assertTrue(search_result_observed('Address: https://www.bing.com/search?q=computer+speed+test'))

    def test_permission_draft_is_not_spoken_and_launch_is_observed(self):
        import io
        agent=server.Agent(lambda *a,**kw:None,'qwen3:8b');calls=[];spoken=[]
        def execute(call):
            calls.append(call['function']['name'])
            if calls[-1]=='desktop_observe':return {'observations':'Edge foreground. Google homepage https://www.google.com/'}
            return {'launch_requested':True,'completion_verified':False}
        agent.state.execute=execute
        def response(message):
            return io.BytesIO((json.dumps({'message':message,'done':True,'done_reason':'stop'})+'\n').encode())
        replies=[response({'content':'Would you like me to proceed?'}),
                 response({'tool_calls':[{'function':{'name':'open_desktop_app','arguments':{'app':'edge','url':'https://www.google.com'}}}]}),
                 response({'content':'Google is visible in Edge.'})]
        with patch.object(agent.connection,'open',side_effect=replies):agent.run('Open Edge and navigate to Google.',spoken.append)
        self.assertEqual(calls,['open_desktop_app','desktop_observe'])
        self.assertNotIn('Would you like',''.join(spoken))
        self.assertIn('Google is visible',''.join(spoken))
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
