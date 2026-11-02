"""Pilot-only extension of existing guarded ThemHands tools."""
import json
import re
from app import State
from conversation import CHAT_TOOLS, tool
from browser_tools import open_browser
from desktop_tools import DESKTOP_TOOLS, DesktopTools
from jsonschema import validate

TOOLS=CHAT_TOOLS+DESKTOP_TOOLS+[
    tool('open_browser_window','ThemHands: open a blank Microsoft Edge window in the Windows running SimplicityAI and verify it appeared. No internet/page-load test or settings changes. Refuse another/outside-host target.'),
    tool('get_tool_capabilities','Read the actual connected ThemHands capabilities and target. No desktop action or diagnostic.')]

CAPABILITIES={
    'name':'ThemHands',
    'role':'The connected local tool layer used by SimplicityAI, already installed in this pilot.',
    'connected':['read-only running-Windows health/network checks','protected Windows file verification (not repair)',
                 'real Calculator controls','open Microsoft Edge blank window and verify its appearance',
                 'Windows-MCP accessibility observation, app switching, observed-control clicking, typing and scrolling',
                 'launch Edge HTTPS websites and supported installed apps; inspect actual result',
                 'create new Desktop text files with exclusive creation and reread verification',
                 'launcher/Lazesoft reference catalog'],
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
        super().__init__();self.desktop=DesktopTools()

    def close(self):self.desktop.close()

    def execute(self,call):
        name=call.get('function',{}).get('name');args=call.get('function',{}).get('arguments',{})
        schema=next((entry['function']['parameters'] for entry in DESKTOP_TOOLS if entry['function']['name']==name),None)
        if schema is not None:
            validate(args,schema);self.check_stop()
            if self.chat.target=='other' and name!='get_recovery_tool_catalog':raise ValueError('That computer is not connected; no desktop action performed')
            self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
            self.emit('action','ThemHands: '+name.replace('_',' ')+' in the Windows running SimplicityAI.')
            result=self.desktop.execute(name,args,self.check_stop)
            self.emit('observation',json.dumps(result));return result
        if name not in {'open_browser_window','get_tool_capabilities'}:return super().execute(call)
        if not isinstance(args,dict) or args:raise ValueError('This tool takes no arguments')
        self.check_stop()
        if name=='get_tool_capabilities':
            result={**CAPABILITIES,'target':self.chat.target}
            result['desktop_runtime']={'initialized':self.desktop.bridge.client is not None,
                                       'loaded_tools':sorted(self.desktop.bridge.names),
                                       'last_observation':self.desktop.snapshot}
            self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
            self.emit('observation',json.dumps(result));return result
        if self.chat.target=='other':raise ValueError('That computer is not connected. No browser was opened.')
        self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
        result=open_browser(self.check_stop,self.emit)
        self.emit('observation',json.dumps(result))
        return result
