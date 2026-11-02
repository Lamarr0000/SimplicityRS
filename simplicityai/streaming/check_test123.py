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

    def test_progressively_released_chat_prefix_is_not_rewritten(self):
        agent=server.Agent(Mock(),'qwen3:8b')
        chunks=[{'message':{'content':'Hello. '},'done':False},
                {'message':{'content':'Is there anything else I can assist you with?'},'done':True,'done_reason':'stop'}]
        response=io.BytesIO(('\n'.join(json.dumps(x) for x in chunks)+'\n').encode())
        with patch.object(agent.connection,'open',return_value=response):agent.run('Hello',lambda _:None)


if __name__=='__main__':unittest.main()
