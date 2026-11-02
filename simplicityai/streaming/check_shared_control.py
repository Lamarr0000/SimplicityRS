"""Voice router and lifecycle regressions. No real desktop/browser input."""
import io
import json
import unittest
from unittest.mock import Mock, patch
import server
from desktop_tools import DesktopTools
from tool_state import ToolState
from target_scope import TargetConversation
from owned_browser import OwnedBrowser


class SharedControlTests(unittest.TestCase):
    def test_observation_after_cancel_does_not_reopen_a_browser(self):
        browser=OwnedBrowser();browser._start=Mock()
        with self.assertRaisesRegex(ValueError,'Open the owned browser'):
            browser.call('observe',{},lambda:None)
        browser._start.assert_not_called()

    def test_owned_search_forces_browser_observation(self):
        agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
        calls=[]
        def execute(call):
            name=call['function']['name'];calls.append(name)
            if name=='search_web':return {'observation_tool':'browser_observe','opened':True}
            if name=='browser_observe':return {'observations':'Observed URL: https://www.google.com/search?q=speed+tests\nSearch results'}
            raise AssertionError(name)
        agent.state.execute=execute
        response=io.BytesIO((json.dumps({'message':{'content':'Search results for speed tests are visible.'},'done':True,'done_reason':'stop'})+'\n').encode())
        with patch.object(agent.connection,'open',return_value=response):
            agent.run('Open a browser and search for speed tests.',lambda _:None)
        self.assertEqual(calls,['search_web','browser_observe'])

    def test_new_tools_obey_outside_machine_scope_and_schema(self):
        state=ToolState();state.chat=TargetConversation();state.chat.target='other'
        state.chat.current_user='On another computer'
        state.desktop.execute=Mock()
        for name,args in [('browser_open',{'url':'https://example.com'}),
                          ('desktop_click_control',{'snapshot':'x','name':'One'})]:
            with self.assertRaises(ValueError):state.execute({'function':{'name':name,'arguments':args}})
        state.desktop.execute.assert_not_called()

    def test_browser_takeover_does_not_restart_or_retry(self):
        desktop=DesktopTools();desktop.bridge=Mock()
        desktop.bridge.call.return_value=json.dumps({'enabled':True,'state':'takeover_pending'})
        desktop.browser=Mock()
        desktop.browser.call.side_effect=lambda op,args,check:check()
        with self.assertRaises(InterruptedError):desktop.execute('browser_open',{'url':'https://example.com'},lambda:None)
        self.assertEqual(desktop.browser.call.call_count,1)

    def test_cancellation_before_request_closes_existing_worker(self):
        browser=OwnedBrowser();browser.close=Mock();browser._start=Mock()
        with self.assertRaises(InterruptedError):browser.call('observe',{},lambda:(_ for _ in ()).throw(InterruptedError('Stop')))
        browser._start.assert_not_called();browser.close.assert_called_once()

    def test_close_releases_browser_and_desktop_driver(self):
        desktop=DesktopTools();desktop.browser=Mock();desktop.bridge=Mock()
        desktop.close()
        desktop.browser.close.assert_called_once();desktop.bridge.close.assert_called_once()


if __name__=='__main__':unittest.main()
