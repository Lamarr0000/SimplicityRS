"""Offline owned-page integration check; no personal profiles or external sites."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_adapter import BrowserAdapter
from control_session import ControlSession, Locator, Condition, AmbiguousControl


def main():
    results=[]
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context()
        # No external network is required or allowed for this local fixture.
        context.route('**/*',lambda route:route.abort())
        page=context.new_page()
        page.set_content('''<label>Test note <input aria-label="Test note"></label>
            <button disabled id="run" onclick="document.querySelector('output').textContent='Complete'">Run test</button>
            <output>Waiting</output><button>Duplicate</button><button>Duplicate</button>
            <script>setTimeout(()=>document.querySelector('#run').disabled=false,350)</script>''')
        session=ControlSession(BrowserAdapter(page))
        results.append(session.act('fill',Locator('Test note','textbox'),text='Local fixture',
                                   expected=Condition(Locator('Test note','textbox'),'value','Local fixture')))
        results.append(session.act('click',Locator('Run test','button'),
                                   expected=Condition(Locator('Complete'),'text','Complete')))
        try:session.act('click',Locator('Duplicate','button'))
        except AmbiguousControl:results.append({'ambiguity_rejected':True})
        else:raise AssertionError('Ambiguous action was not rejected')
        assert all(row.get('outcome_verified',row.get('ambiguity_rejected',False)) for row in results)
        context.close();browser.close()
    path=Path('C:/SimplicityAI-Lab/ControlAdapter/browser-check.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'checks':len(results),'report':str(path)}))


if __name__=='__main__':main()
