"""Pilot-only extension of existing guarded ThemHands tools."""
import json
import re
from app import State
from conversation import CHAT_TOOLS, tool
from browser_tools import open_browser
from desktop_tools import DESKTOP_TOOLS, DesktopTools
from jsonschema import validate
from session_tools import export_conversation,sample_cpu
from windows_baseline import BASELINE_TOOLS,inspect_windows
from troubleshooting import guidance
from findings import table_view,table_text

TOOLS=CHAT_TOOLS+DESKTOP_TOOLS+BASELINE_TOOLS+[
    tool('get_tool_capabilities','Read the actual connected ThemHands capabilities and target. No desktop action or diagnostic.')]

CAPABILITIES={
    'name':'ThemHands',
    'role':'The connected local tool layer used by SimplicityAI, already installed in this pilot.',
    'connected':['read-only running-Windows health/network checks','protected Windows file verification (not repair)',
                 'real Calculator controls','owned Edge browser navigation and fresh page observations',
                 'Windows-MCP accessibility observation, app switching, observed-control clicking, typing and scrolling',
                 'launch Edge HTTPS websites and supported installed apps; inspect actual result',
                 'create new Desktop text files with exclusive creation and reread verification',
                 'export app-recorded conversation, both speakers, without model reconstruction',
                 'launch Task Manager; read-only sampled per-process CPU ranking',
                 'focused system/storage/device/driver/service/event/update/security/startup diagnostics',
                 'launcher/Lazesoft reference catalog','named Windows control lookup/readiness checks',
                 'owned temporary Edge context with Playwright structured page controls'],
    'not_connected':['visual interpretation of inaccessible/custom controls','validated Lazesoft recovery workflows',
                     'repairs','another/offline Windows installation'],
    'desktop_driver':'Local stdio Windows-MCP; lazy initialization verifies actual tool registration; failure is reported, never simulated',
    'browser_launch_is_not_internet_test':True}


def capability_reply(text):
    """Answer narrow install/identity questions from actual app facts, not guesses."""
    if not re.search(r'\bthem\s*hands\b',text,re.I):return None
    if not re.search(r'\b(install|what (?:is|are)|need(?:\s+\w+){0,4}\s+tools?)\b',text,re.I):return None
    if re.match(r'\s*(?:please\s+)?(?:use|open|launch|check|calculate|verify)\b',text,re.I):return None
    return ('ThemHands is already connected. It is my local tool layer for Windows and network checks, '
            'protected-file verification, and desktop assistance. I can observe accessible controls, click, type, '
            'scroll, switch windows, open supported apps and websites, and create new Desktop text files. '
            'Actions need actual tool evidence. Lazesoft recovery workflows are catalogued but not yet validated.')


class ToolState(State):
    def __init__(self):
        super().__init__();self.desktop=DesktopTools();self.recent_findings={}

    def close(self):self.desktop.close()

    def execute(self,call):
        name=call.get('function',{}).get('name');args=call.get('function',{}).get('arguments',{})
        schema=next((entry['function']['parameters'] for entry in DESKTOP_TOOLS+BASELINE_TOOLS if entry['function']['name']==name),None)
        if schema is not None:
            validate(args,schema);self.check_stop()
            local_actions={'desktop_observe','desktop_switch','desktop_interact','desktop_click_control','browser_open','browser_observe','browser_act','browser_wait','close_app_windows','open_desktop_app','search_web','create_desktop_text','export_conversation','list_windows','manage_window'}
            from target_scope import OTHER
            explicitly_other=OTHER.search(self.chat.current_user or '')
            if self.chat.target=='other' and name not in {'get_recovery_tool_catalog','get_recent_findings'} and (name not in local_actions or explicitly_other or not self.chat.current_user):raise ValueError('The affected Windows is not connected. Current recovery-environment checks would not diagnose that installation.')
            self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
            self.emit('action','ThemHands: '+name.replace('_',' ')+' in the Windows running SimplicityAI.')
            try:
                if name=='export_conversation':result=export_conversation(self.chat.transcript,args.get('filename'))
                elif name=='get_cpu_process_snapshot':result=sample_cpu(self.check_stop)
                elif name=='inspect_windows':result=inspect_windows(args['area'],args.get('query',''),self.check_stop)
                elif name=='get_recent_findings':result={'source':'earlier session evidence, not a new check','findings':list(self.recent_findings.values())}
                else:result=self.desktop.execute(name,args,self.check_stop)
            except InterruptedError:raise
            except Exception as error:
                self.emit('observation',json.dumps({'tool':name,'ok':False,'error':str(error)}));raise
            if name in {'inspect_windows','get_cpu_process_snapshot'}:
                area=args['area'] if name=='inspect_windows' else 'processes'
                recorded=result if name=='inspect_windows' else {**result,'area':area}
                self.recent_findings.pop(area,None)
                self.recent_findings[area]=recorded
                view=table_view(recorded)
                self.chat.transcript.append({'id':len(self.chat.transcript),'role':'assistant','kind':'measured_facts','content':table_text(view)})
                self.emit('findings',json.dumps(view))
            self.emit('observation',json.dumps(result));return result
        if name=='calculate_in_calculator' and self.chat.target=='other':
            from target_scope import OTHER
            if OTHER.search(self.chat.current_user):raise ValueError('Another computer is not connected')
            self.chat.target='current'
            try:return super().execute(call)
            finally:self.chat.target='other'
        if name not in {'open_browser_window','get_tool_capabilities'}:return super().execute(call)
        if not isinstance(args,dict) or args:raise ValueError('This tool takes no arguments')
        self.check_stop()
        if name=='get_tool_capabilities':
            result={**CAPABILITIES,'target':self.chat.target}
            result['registered_tools']=[entry['function']['name'] for entry in TOOLS]
            result['troubleshooting_approach']=guidance('')
            result['desktop_runtime']={'initialized':self.desktop.bridge.client is not None,
                                       'loaded_tools':sorted(self.desktop.bridge.names),
                                       'last_observation':self.desktop.snapshot,
                                       'owned_browser_running':self.desktop.browser.process is not None and self.desktop.browser.process.poll() is None}
            self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
            self.emit('observation',json.dumps(result));return result
        if self.chat.target=='other':raise ValueError('That computer is not connected. No browser was opened.')
        self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
        result=self.desktop.execute('browser_open',{'url':'about:blank'},self.check_stop)
        self.emit('observation',json.dumps(result))
        return result
