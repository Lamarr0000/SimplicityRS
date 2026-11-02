"""Opt-in owned-worker integration against offline fixture. Never records audio."""
import json
import psutil
from pathlib import Path
from owned_browser import OwnedBrowser
from desktop_tools import DesktopTools


def main():
    browser=OwnedBrowser(fixture=True)
    desktop=DesktopTools()
    desktop.browser=browser
    call=desktop.browser_call
    results=[]
    check=lambda:None
    try:
        results.append(call('open',{'url':'https://fixture.invalid/'},check))
        observed=call('observe',{},check)
        results.append({'observed_fixture':'Local control check' in observed['observations']})
        waited=call('wait',{'text':'Ready result 42 Mbps','seconds':2},check)
        assert waited['condition_met'] and 'Visible page text' in waited['observations']
        results.append({'asynchronous_result_observed':True})
        for url in ('file:///C:/private.txt','javascript:alert(1)','https://user:pass@example.com'):
            try:call('open',{'url':url},check)
            except ValueError:pass
            else:raise AssertionError('Unsafe browser URL was accepted')
        observed=call('observe',{},check)
        assert observed['url']=='https://fixture.invalid/'
        results.append({'unsafe_urls_rejected_without_navigation':True})
        results.append(call('act',{'snapshot':observed['snapshot'],'action':'fill','role':'textbox','name':'Test note','text':'Owned local test'},check))
        observed=call('observe',{},check)
        results.append(call('act',{'snapshot':observed['snapshot'],'action':'click','role':'button','name':'Run test','expected_text':'Complete'},check))
        observed=call('observe',{},check)
        assert 'Complete' in observed['observations']
        try:call('act',{'snapshot':observed['snapshot'],'action':'click','role':'button','name':'Delete'},check)
        except ValueError:results.append({'consequential_action_rejected':True})
        else:raise AssertionError('Consequential action was allowed')
        assert browser.process is not None
        results.append({'no_input_refusal_keeps_context':True})
        recovered=call('observe',{},check)
        assert 'Complete' in recovered['observations']
        # New navigation is explicit; a refusal never replays the rejected action.
        call('open',{'url':'https://fixture.invalid/'},check)
        pid=browser.process.pid
        owned=[psutil.Process(pid),*psutil.Process(pid).children(recursive=True)]
        try:call('observe',{},lambda:(_ for _ in ()).throw(InterruptedError('Test stop')))
        except InterruptedError:results.append({'cancelled_worker_closed':browser.process is None,'pid':pid})
        else:raise AssertionError('Cancellation was ignored')
        _,alive=psutil.wait_procs(owned,timeout=3)
        assert not alive,'An owned browser descendant survived cancellation'
        results.append({'owned_descendants_closed':True})
    finally:desktop.close()
    path=Path('C:/SimplicityAI-Lab/ControlAdapter/voice-owned-browser-check.json')
    path.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'report':str(path)}))


if __name__=='__main__':main()
