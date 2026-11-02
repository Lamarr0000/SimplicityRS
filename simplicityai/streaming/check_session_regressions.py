"""Multi-turn regressions from live conversation; no real desktop action."""
import asyncio
import io
import json
import unittest
from unittest.mock import Mock,patch,AsyncMock
import server
from target_scope import TargetConversation
from intent_control import cancelled,continuation,arithmetic,window_request,repeated_target_question
from desktop_workflow import requested_app
from desktop_tools import foreground_lines
from window_control import WindowControl


class SessionRegressionTests(unittest.TestCase):
    def test_real_scope_wording_confirms_once(self):
        for text in ["YES I'M REFERRING TO THE WINDOWS INSTALLATION THAT IS RUNNING SIMPLICITY A I", "JUST RUN A DIAGNOSTIC ON THE COMPUTER THAT'S RUNNING SIMPLICITY A I",'For this exercise I mean this computer.']:
            chat=TargetConversation();chat.begin(text);self.assertEqual(chat.target,'current',text)
            chat.begin('Yes');self.assertEqual(chat.target,'current')
        chat=TargetConversation();chat.begin('Not the Windows installation that is running SimplicityAI.');self.assertEqual(chat.target,'other')
        self.assertFalse(repeated_target_question('The Windows running SimplicityAI is confirmed; no further target confirmation is needed. What boot error do you see?'))
        self.assertTrue(repeated_target_question('Could you please confirm which Windows environment you mean?'))

    def test_calculation_routes_to_verified_tool(self):
        self.assertEqual(arithmetic('Open Calculator and execute one plus one'),'1+1')
        self.assertEqual(arithmetic('Open Calculator and show seven times seven'),'7*7')
        self.assertIsNone(arithmetic('Calculator one plus one plus one'))
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.execute=Mock(return_value={'display':'2','simulation':True})
        with patch.object(agent.connection,'open',side_effect=AssertionError('No planning model needed')):agent.run('Open Calculator and execute one plus one',lambda text:None)
        self.assertEqual(agent.state.execute.call_args.args[0]['function']['name'],'calculate_in_calculator')

    def test_cancelled_request_cannot_launch_again(self):
        self.assertTrue(cancelled("Don't even worry about it"));self.assertTrue(cancelled('Never mind, I closed it already'))
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.execute=Mock()
        with patch.object(agent.connection,'open',side_effect=AssertionError('No model call after cancellation')):agent.run("Don't even worry about it",lambda text:None)
        agent.state.execute.assert_not_called();self.assertTrue(agent.actions_paused)

    def test_foreground_controls_exclude_taskbar(self):
        tree='desktop\n    ├── window "Calculator"\n    │   └── (10,20) button "One" [action: click]\n    └── window "Taskbar"\n        └── (30,40) button "Calculator - 1 running window" [action: click]'
        active=[line for line,inside in foreground_lines(tree,'Calculator') if inside and '[action:' in line]
        self.assertEqual(len(active),1);self.assertIn('"One"',active[0])

    def test_window_minimize_preserves_actual_assistant_not_vm_title(self):
        control=WindowControl();control.when=__import__('time').monotonic()
        control.observed={'a':{'handle':1,'pid':1,'created':10,'title':'SimplicityAI','own':True},'v':{'handle':2,'pid':2,'created':10,'title':'SimplicityAI Windows 11 - VMware Workstation','own':False}}
        with patch('window_control.win32gui.IsWindow',return_value=True),patch('window_control.win32gui.GetWindowText',return_value='SimplicityAI Windows 11 - VMware Workstation'),patch('window_control.psutil.Process') as process,patch('window_control.win32gui.ShowWindow') as show,patch('window_control.win32gui.IsIconic',return_value=True):
            process.return_value.create_time.return_value=10
            result=control.manage('minimize_others',None,lambda:None)
        show.assert_called_once();self.assertEqual(show.call_args.args[0],2);self.assertTrue(result['all_verified'])

    def test_window_requests_and_utility_spelling(self):
        self.assertEqual(window_request('Minimise everything open except yourself'),'minimize_others')
        self.assertEqual(window_request('Close the Fast browser please'),'close_browser')
        self.assertEqual(requested_app('Open up the device manger'),'device_manager')
        self.assertTrue(continuation('Open Device Manager and give me a list of','working drivers that I have'))

    def test_close_uses_normal_window_message_and_verifies(self):
        control=WindowControl();control.when=__import__('time').monotonic()
        control.observed={'b':{'handle':9,'pid':2,'created':10,'title':'Fast.com - Edge','own':False}}
        with patch('window_control.win32gui.IsWindow',side_effect=[True,False,False]),patch('window_control.win32gui.GetWindowText',return_value='Fast.com - Edge'),patch('window_control.psutil.Process') as process,patch('window_control.win32gui.PostMessage') as close:
            process.return_value.create_time.return_value=10;result=control.manage('close','b',lambda:None)
        self.assertEqual(close.call_args.args[0],9);self.assertTrue(result['all_verified'])
        process.return_value.kill.assert_not_called()

    def test_window_manager_will_not_close_itself_or_guess_an_id(self):
        control=WindowControl();control.when=__import__('time').monotonic()
        control.observed={'a':{'handle':9,'pid':2,'created':10,'title':'SimplicityAI','own':True}}
        with patch('window_control.win32gui.PostMessage') as close:
            with self.assertRaises(ValueError):control.manage('close','unknown',lambda:None)
            with self.assertRaises(ValueError):control.manage('close','a',lambda:None)
            close.assert_not_called()


class VoiceSessionRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_clears_pending_without_starting_actor(self):
        class Socket:
            async def send_json(self,value):pass
        session=server.Session(Socket(),'qwen3:8b',io.StringIO());session.pending=('old task','voice');session.agent.diagnostic_pending=True
        await session.submit("Don't even worry about it",'voice')
        self.assertIsNone(session.pending);self.assertIsNone(session.actor);self.assertFalse(session.agent.diagnostic_pending)
        self.assertTrue(session.agent.actions_paused)

    async def test_voice_continuation_retains_the_original_action(self):
        class Socket:
            async def send_json(self,value):pass
        session=server.Session(Socket(),'qwen3:8b',io.StringIO());session.turn_loop=AsyncMock()
        await session.submit('Open Calculator and execute one plus one','voice');await asyncio.sleep(0)
        await session.submit('Tell me the results','voice')
        self.assertIn('Open Calculator',session.pending[0]);self.assertIn('Tell me the results',session.pending[0])
        await asyncio.sleep(0)


if __name__=='__main__':unittest.main()
