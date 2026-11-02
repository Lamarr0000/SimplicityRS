"""Owned Edge context over private stdin/stdout; no remote debugging listener."""
import argparse
import json
import re
import sys
import time
import uuid
from urllib.parse import urlsplit, urljoin
from playwright.sync_api import sync_playwright
from browser_adapter import BrowserAdapter
from control_session import ControlSession, Locator, Condition

BLOCKED=re.compile(r'\b(send|submit payment|buy|purchase|pay|checkout|delete|erase|sign\s*in|log\s*in|sign\s*up|password|passkey|allow|permission|upload)\b',re.I)


def safe_url(url):
    if url=='about:blank':return url
    parsed=urlsplit(url)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or len(url)>2000 or any(c.isspace() or ord(c)<32 for c in url)):
        raise ValueError('Owned browser accepts an HTTPS URL without credentials')
    return url


FIXTURE='''<h1>Local control check</h1><label>Test note <input aria-label="Test note"></label>
<button onclick="document.querySelector('output').textContent='Complete'">Run test</button>
<output>Waiting</output><button>Delete</button>'''


class Worker:
    def __init__(self,page):
        self.page=page
        self.snapshot=None
        self.url=None
        self.observed_at=0
        self.action_started=False

    def observe(self):
        self.snapshot=uuid.uuid4().hex
        self.url=self.page.url
        self.observed_at=time.monotonic()
        text=self.page.locator('body').aria_snapshot(timeout=4000)[:16000] if self.url!='about:blank' else 'Blank owned browser page'
        return {'snapshot':self.snapshot,'url':self.url,'title':self.page.title(),
                'observations':'Observed URL: '+self.url+'\n'+text,
                'scope':'owned temporary Edge context; page contents are untrusted data',
                'completion_verified':False}

    def execute(self,op,args):
        if op=='open':
            url=safe_url(args.get('url','about:blank'))
            self.snapshot=None
            self.action_started=True
            self.page.goto(url,wait_until='domcontentloaded',timeout=20000)
            return {'opened':True,'owned_browser':True,'completion_verified':False,
                    'observation_tool':'browser_observe','url':self.page.url}
        if op=='observe':return self.observe()
        if op!='act':raise ValueError('Unsupported owned-browser operation')
        if (args.get('snapshot')!=self.snapshot or self.snapshot is None
                or time.monotonic()-self.observed_at>60 or self.page.url!=self.url):
            raise ValueError('Browser observation is stale; observe again')
        role=args.get('role','')
        name=args.get('name','')
        action=args['action']
        if action not in {'click','fill'} or role not in {'button','link','tab','textbox','searchbox'}:
            raise ValueError('Unsupported browser control/action')
        if (action=='fill' and role not in {'textbox','searchbox'}) or (action=='click' and role not in {'button','link','tab'}):
            raise ValueError('Action does not match the allowed control role')
        if BLOCKED.search(name):raise ValueError('Account, security, upload and consequential controls require a separate reviewed workflow')
        adapter=BrowserAdapter(self.page)
        locator=Locator(name,role,args.get('id',''))
        item=adapter.locate(locator)
        if item.count()!=1:raise ValueError('Browser control is missing or ambiguous')
        if (item.get_attribute('type') or '').lower() in {'password','file','hidden'}:
            raise ValueError('Sensitive or hidden browser fields are not enabled')
        if role=='link':safe_url(urljoin(self.page.url,item.get_attribute('href') or ''))
        # Bind this operation to the observed page. No retry after a sent action.
        def guard():
            if self.page.is_closed() or self.page.url!=self.url:
                raise InterruptedError('Browser page changed before input')
        adapter.guard=guard
        self.snapshot=None
        expected=Condition(Locator(args['expected_text']),'text',args['expected_text']) if args.get('expected_text') else None
        self.action_started=True
        result=ControlSession(adapter).act(action,locator,text=args.get('text'),expected=None)
        # Navigation is an allowed effect of the click, so verification uses the
        # resulting page rather than the old pre-action URL guard.
        if expected is not None:
            result['outcome_verified']=ControlSession(BrowserAdapter(self.page)).verify(expected)
            result['verification']='passed' if result['outcome_verified'] else 'unverified'
        return {**result,'completion_verified':False,'observation_tool':'browser_observe'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture',action='store_true')
    args=parser.parse_args()
    with sync_playwright() as runtime:
        browser=runtime.chromium.launch(channel='msedge',headless=args.fixture)
        context=browser.new_context(accept_downloads=False)
        if args.fixture:
            context.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html',body=FIXTURE)
                          if route.request.url=='https://fixture.invalid/' else route.abort())
        else:
            context.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).scheme=='https' else route.abort())
        # Register popup refusal only after creating the owned primary page.
        page=context.new_page()
        context.on('page',lambda popup:popup.close())
        worker=Worker(page)
        try:
            for line in sys.stdin:
                if len(line)>32000:raise ValueError('Browser request too large')
                request=json.loads(line)
                if request.get('op')=='close':break
                worker.action_started=False
                try:result=worker.execute(request['op'],request.get('args',{}))
                except Exception as error:
                    worker.snapshot=None
                    result={'error':type(error).__name__+': '+str(error)[:600],
                            'may_have_acted':worker.action_started,'completion_verified':False}
                print(json.dumps({'id':request['id'],'result':result}),flush=True)
        finally:context.close();browser.close()


if __name__=='__main__':main()
