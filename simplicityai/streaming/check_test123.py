"""Reported test123 regressions. Browser/collector/Calculator effects simulated."""
import io
import json
import unittest
from unittest.mock import Mock,patch
import server
from intent_control import arithmetic,retry_arithmetic
from desktop_workflow import web_search_request,search_result_observed
from troubleshooting import requested_checks,diagnostic_report_issue


class ReportedTests(unittest.TestCase):
    def test_numeric_x_forms_use_existing_verified_calculator(self):
        for text in ('execute 7 x7','execute 7 x 7','calculate 7 X 7'):
            self.assertEqual(arithmetic(text),'7*7')
        self.assertIsNone(arithmetic('calculate -7 + 7'))
        self.assertIsNone(arithmetic('calculate 7 x 7 + 1'))
        agent=server.Agent(Mock(),'qwen3:8b')
        agent.state.execute=Mock(side_effect=[InterruptedError('Simulated interruption'),{'display':'49','simulation':True}])
        with patch.object(agent.connection,'open',side_effect=AssertionError('No planning model needed')):
            with self.assertRaises(InterruptedError):agent.run('can you open calculator and execute 7 x7 and tell me what it displays?',lambda _:None)
            agent.run('I might have interrupted. try again.',lambda _:None)
        self.assertEqual([c.args[0]['function']['name'] for c in agent.state.execute.call_args_list],['calculate_in_calculator']*2)

    def test_retry_does_not_resurrect_cancelled_arithmetic(self):
        history=[{'role':'user','content':'calculate 7 x 7'},{'role':'user','content':'cancel'}]
        self.assertIsNone(retry_arithmetic('try again',history))

    def test_spoken_search_alias_and_google_challenge_are_distinguished(self):
        self.assertEqual(web_search_request('OPEN UP A BROWSER AND GOGGLE SEARCH SPEED TEST'),'SPEED TEST')
        self.assertFalse(search_result_observed('Observed URL: https://www.google.com/sorry/index?q=challenge-token'))
        agent=server.Agent(Mock(),'qwen3:8b');calls=[];spoken=[]
        def execute(call):
            name=call['function']['name'];calls.append(name)
            return {'observation_tool':'browser_observe'} if name=='search_web' else {'blocker':{'kind':'human_verification'}}
        agent.state.execute=execute
        with patch.object(agent.connection,'open',side_effect=AssertionError('No invention after a known verification blocker')):
            agent.run('OPEN UP A BROWSER AND GOGGLE SEARCH SPEED TEST',spoken.append)
        self.assertEqual(calls,['search_web','browser_observe'])
        self.assertIn('verification',' '.join(spoken));self.assertIn('not reached',' '.join(spoken))

    def test_driver_good_question_collects_and_reports_without_health_overclaim(self):
        prompt='can you open device manager and tell me if my drivers are good'
        self.assertEqual(requested_checks(prompt),{'devices','drivers'})
        agent=server.Agent(Mock(),'qwen3:8b');calls=[];spoken=[]
        def execute(call):
            name=call['function']['name'];calls.append(name)
            if name=='inspect_windows':
                area=call['function']['arguments']['area']
                data=[{'ConfigManagerErrorCode':0}] if area=='devices' else [{'IsSigned':True},{'IsSigned':None}]
                result={'simulation':True,'sections':[{'status':'available','data':data}]}
                agent.state.recent_findings[area]=result
                return result
            return {'observations':'Device Manager launch requested; source observations are simulated'}
        agent.state.execute=execute
        with patch.object(agent.connection,'open',side_effect=AssertionError('Measured report does not require model reconstruction')):
            agent.run(prompt,spoken.append)
            agent.run('what does that mean?',spoken.append)
            agent.run('thanks',spoken.append)
        text=' '.join(spoken)
        self.assertIn('does not prove',text);self.assertIn('unknown signing',text)
        self.assertNotIn('functioning correctly',text)
        self.assertEqual(calls.count('inspect_windows'),2)
        self.assertTrue(diagnostic_report_issue('The drivers listed are all signed and functioning correctly.',{'drivers'}))

    def test_driver_status_wording_requests_both_collectors(self):
        for prompt in ['THE DRIVER STATUS OF MY DEVICES','OPEN THE VICE MANAGER AND LET ME KNOW THE STATUS OF MY DRIVERS']:
            self.assertEqual(requested_checks(prompt),{'devices','drivers'})
        self.assertEqual(requested_checks("don't check the driver status"),set())

    def test_output_audio_requests_do_not_become_scope_acknowledgments_or_fake_checks(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.chat.target='current'
        agent.state.execute=Mock(side_effect=AssertionError('No endpoint tool exists'))
        with patch.object(agent.connection,'open',side_effect=AssertionError('No invented audio checks')):
            for prompt in ['PLEASE UNMUTE THIS COMPUTER','I cannot hear your voice','check basic sound settings','increase volume by fifty percent']:
                spoken=[];agent.run(prompt,spoken.append)
                self.assertIn('cannot read or change',' '.join(spoken))
                self.assertNotIn('confirmed',' '.join(spoken))

    def test_late_control_dump_is_neither_spoken_nor_executed(self):
        spoken=[];events=[]
        agent=server.Agent(lambda kind,**data:events.append((kind,data)),'qwen3:8b')
        agent.state.execute=Mock(side_effect=AssertionError('Text is never a tool call'))
        chunks=[{'message':{'content':'Let me explain what I see. '},'done':False},
                {'message':{'content':'[control 98] (2912,36) button "Minimize" [action: click]'},'done':True}]
        response=io.BytesIO(('\n'.join(json.dumps(x) for x in chunks)+'\n').encode())
        with patch.object(agent.connection,'open',return_value=response):agent.run('help with this window',spoken.append)
        visible=' '.join(data.get('text','') for kind,data in events if kind=='text.delta')
        self.assertNotIn('[control',visible);self.assertNotIn('Let me explain',visible)
        self.assertNotIn('[action',' '.join(spoken));self.assertIn('unverified',visible)
        agent.state.execute.assert_not_called()

    def test_output_guard_preserves_ordinary_explanations(self):
        from protocol import internal_output
        self.assertFalse(internal_output('Calculator shows 49.'))
        self.assertFalse(internal_output('Example Python: ```print(49)```'))
        self.assertTrue(internal_output('```click(42)```',control_task=True))
        self.assertTrue(internal_output('{"function": {"name": "desktop_interact", "arguments": {}}}'))

    def test_speech_test_is_supported_without_claiming_access_to_raw_audio(self):
        agent=server.Agent(Mock(),'qwen3:8b');spoken=[]
        with patch.object(agent.connection,'open',side_effect=AssertionError('Application speech help is grounded')):
            agent.run('This is a test to see how well you can detect audio and slurt words',spoken.append)
        self.assertIn('we can test',' '.join(spoken))
        self.assertIn('recognized text',' '.join(spoken))
        self.assertNotIn('not to test',' '.join(spoken))

    def test_spoken_session_export_uses_recorded_transcript_not_model_file(self):
        from task_agenda import conversation_export_request,export_filename
        prompt='CREATED COPY OF THIS ENTIRE CHATCESSION SAVE IN ALL MY DES TOP AS FIVE SIX SEVENTY EIGHT'
        self.assertTrue(conversation_export_request(prompt))
        self.assertEqual(export_filename(prompt),'FIVE SIX SEVENTY EIGHT.txt')
        self.assertFalse(conversation_export_request('do not save this chat'))
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.execute=Mock(return_value={'message_count':12,'path':'simulated export.txt'})
        with patch.object(agent.connection,'open',side_effect=AssertionError('Never reconstruct transcript')):
            agent.run(prompt,lambda _:None)
        self.assertEqual(agent.state.execute.call_args.args[0]['function']['name'],'export_conversation')
        agent.state.chat.current_user=prompt
        from tool_state import ToolState
        with self.assertRaisesRegex(ValueError,'model-written'):
            ToolState.execute(agent.state,{'function':{'name':'create_desktop_text','arguments':{'filename':'session.txt','content':'incomplete summary'}}})

    def test_backup_request_does_not_invent_tools(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.state.execute=Mock(side_effect=AssertionError('No backup capability'))
        spoken=[]
        with patch.object(agent.connection,'open',side_effect=AssertionError('Capability limitation is application owned')):
            agent.run('create a backup copy of my drivers on my desktop',spoken.append)
            agent.run('use those third party tools that you recommended',spoken.append)
        self.assertIn('no driver backup files were created',' '.join(spoken))
        self.assertIn('SFC do not back up',' '.join(spoken))

    def test_progressively_released_chat_prefix_is_not_rewritten(self):
        agent=server.Agent(Mock(),'qwen3:8b')
        chunks=[{'message':{'content':'Hello. '},'done':False},
                {'message':{'content':'Is there anything else I can assist you with?'},'done':True,'done_reason':'stop'}]
        response=io.BytesIO(('\n'.join(json.dumps(x) for x in chunks)+'\n').encode())
        with patch.object(agent.connection,'open',return_value=response):agent.run('Hello',lambda _:None)


class ExitTests(unittest.IsolatedAsyncioTestCase):
    async def test_exit_is_explicit_and_uses_session_event_without_model_or_window_guessing(self):
        from intent_control import exit_request
        for text in ['Close yourself','please close yourself','quit this app','exit SimplicityAI','Turn yourself off please','Turn yourself off','switch yourself off']:
            self.assertTrue(exit_request(text))
        for text in ['do not close yourself','close Calculator','explain how to close yourself','Said they','close yourself and delete my files']:
            self.assertFalse(exit_request(text))
        ws=Mock();ws.send_json=__import__('unittest.mock',fromlist=['AsyncMock']).AsyncMock()
        session=server.Session(ws,'qwen3:8b',io.StringIO())
        session.agent.run=Mock(side_effect=AssertionError('No model needed'))
        session.agent.state.desktop.browser.close=Mock()
        await session.submit('Close yourself',source='voice')
        self.assertFalse(session.listening)
        self.assertIsNone(session.pending)
        self.assertIsNone(session.actor)
        self.assertTrue(session.agent.state.cancel.is_set())
        self.assertEqual(ws.send_json.call_args.args[0]['type'],'app.exit')


if __name__=='__main__':unittest.main()
