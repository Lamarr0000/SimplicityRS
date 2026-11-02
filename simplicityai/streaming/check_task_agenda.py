"""Regressions from the43-message live export; actions below are simulated."""
import io
import json
import unittest
from unittest.mock import Mock, patch
import server
from task_agenda import TaskAgenda, close_intent, export_filename
from intent_control import window_request
from intent_control import cancelled
from desktop_tools import DesktopTools

ORIGINAL='can you close my calculator app, open a browser and conduct a speed test at fast.com'


def reply(text):
    return io.BytesIO((json.dumps({'message':{'content':text},'done':True,'done_reason':'stop'})+'\n').encode())


class TaskAgendaTests(unittest.TestCase):
    def test_closed_before_navigation_recovers_once_without_replaying_sent_action(self):
        from owned_browser import OwnedBrowser
        class Client(OwnedBrowser):
            def __init__(self):super().__init__();self.starts=0;self.writes=0
            def _start(self):
                self.starts+=1
                owner=self
                class Input:
                    def write(self,data):
                        owner.writes+=1;request=json.loads(data)
                        result=({'error':'Page was already closed','may_have_acted':False,'closed_before_action':True}
                                if owner.starts==1 else {'opened':True})
                        owner.responses.put({'id':request['id'],'result':result})
                    def flush(self):pass
                self.process=Mock();self.process.stdin=Input();self.process.poll.return_value=None
            def close(self):self.process=None
        client=Client()
        self.assertTrue(client.call('open',{'url':'https://example.com'},lambda:None)['opened'])
        self.assertEqual(client.starts,2)
        self.assertEqual(client.writes,2)

    def test_large_browser_evidence_is_bounded_without_erasing_latest_values(self):
        from evidence_context import model_evidence
        evidence={'snapshot':'observed','url':'https://example.com',
                  'observations':'HEAD'+('x'*20000)+'TAIL',
                  'visible_text':('y'*10000)+'42 Mbps'}
        result=model_evidence(evidence,1200)
        self.assertLessEqual(len(result),1200)
        data=json.loads(result)
        self.assertTrue(data['model_context_truncated'])
        self.assertIn('42 Mbps',data['visible_text'])
        self.assertEqual(data['snapshot'],'observed')
        self.assertEqual(len(evidence['observations']),20008)

    def test_times_up_cancels_instead_of_leaving_a_resumable_goal(self):
        self.assertTrue(cancelled('times up. sorry.'))
        self.assertFalse(cancelled("What happens when time's up?"))

    def test_close_verb_binds_to_named_app_not_later_browser(self):
        self.assertEqual(close_intent(ORIGINAL),{'app':'calculator','all':False})
        self.assertIsNone(window_request(ORIGINAL))
        self.assertEqual(close_intent('close all browses window but leave apps open'),{'app':'browser','all':True})
        self.assertIsNone(close_intent("Don't close the browser"))

    def test_followups_keep_goal_but_ui_question_does_not_execute_it(self):
        agenda=TaskAgenda();agenda.begin(ORIGINAL)
        self.assertEqual(agenda.url,'https://fast.com')
        for text in ('proceed','use edge','do it','yes please','yes do it now please',
                     'do all required steps consecutively','look at the screen and explain the results'):
            self.assertTrue(agenda.related(text),text)
        self.assertFalse(agenda.related('why is the word proceed stuck at the bottom of this chat ?'))
        agenda.clear();self.assertFalse(agenda.related('proceed'))

    def test_multiturn_routes_close_open_observe_then_fresh_results_without_reopening(self):
        agent=server.Agent(Mock(),'qwen3:8b');calls=[]
        def execute(call):
            name=call['function']['name'];calls.append((name,call['function']['arguments']))
            if name=='close_app_windows':return {'all_verified':True,'matched_windows':1}
            if name=='browser_open':return {'opened':True,'observation_tool':'browser_observe'}
            if name=='browser_observe':return {'observations':'Observed URL: https://fast.com/\nVisible page text: Download42 Mbps'}
            raise AssertionError(name)
        agent.state.execute=execute
        with patch.object(agent.connection,'open',side_effect=[reply('The page currently displays42 Mbps.'),reply('The freshly read download result is42 Mbps.')]):
            agent.run(ORIGINAL,lambda _:None)
            agent.run('the test has been complete. please look at the screen and explain the results',lambda _:None)
        self.assertEqual([name for name,args in calls],['close_app_windows','browser_open','browser_observe','browser_observe'])
        self.assertEqual(calls[0][1]['app'],'calculator')

    def test_export_honors_actual_with_the_name_wording(self):
        self.assertEqual(export_filename('create a full copy of this entire chat session and save it on the desk with the name New Feature Test.'),'New Feature Test.txt')

    def test_close_all_browsers_leaves_native_apps_out_of_selection(self):
        desktop=DesktopTools();desktop.windows=Mock();desktop.browser=Mock();desktop.browser.process=None
        desktop.windows.observe.return_value={'windows':[{'id':'edge','process':'msedge.exe','title':'Page'},
            {'id':'calc','process':'CalculatorApp.exe','title':'Calculator'},
            {'id':'notepad','process':'Notepad.exe','title':'Notes'}]}
        desktop.windows.manage.return_value={'results':[{'title':'Page','verified':True}]}
        result=desktop.execute('close_app_windows',{'app':'browser','all':True},lambda:None)
        self.assertTrue(result['all_verified'])
        self.assertEqual(desktop.windows.manage.call_args.args[:2],('close','edge'))

    def test_unavailable_result_page_is_not_reported_as_running(self):
        agent=server.Agent(Mock(),'qwen3:8b');agent.agenda.begin(ORIGINAL);agent.agenda.opened=True;agent.agenda.close_done=True
        agent.state.execute=Mock(return_value={'error':'Target page closed'})
        spoken=[]
        with patch.object(agent.connection,'open',side_effect=AssertionError('No model invention after page failure')):
            agent.run('look at the screen and explain the results',spoken.append)
        self.assertIn('no longer available',''.join(spoken))
        self.assertNotIn('running',''.join(spoken))


if __name__=='__main__':unittest.main()
