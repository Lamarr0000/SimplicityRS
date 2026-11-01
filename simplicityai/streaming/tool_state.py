"""Pilot-only extension of existing guarded ThemHands tools."""
import json
import re
from app import State
from conversation import CHAT_TOOLS, tool
from browser_tools import open_browser

TOOLS=CHAT_TOOLS+[
    tool('open_browser_window','ThemHands: open a blank Microsoft Edge window in the Windows running SimplicityAI and verify it appeared. No internet/page-load test or settings changes. Refuse another/outside-host target.'),
    tool('get_tool_capabilities','Read the actual connected ThemHands capabilities and target. No desktop action or diagnostic.')]

CAPABILITIES={
    'name':'ThemHands',
    'role':'The connected local tool layer used by SimplicityAI, already installed in this pilot.',
    'connected':['read-only running-Windows health/network checks','protected Windows file verification (not repair)',
                 'real Calculator controls','open Microsoft Edge blank window and verify its appearance'],
    'not_connected':['arbitrary app/file control','browser page navigation or reading','repairs','another/offline Windows installation'],
    'browser_launch_is_not_internet_test':True}


def capability_reply(text):
    """Answer narrow install/identity questions from actual app facts, not guesses."""
    if not re.search(r'\bthem\s*hands\b',text,re.I):return None
    if not re.search(r'\b(install|what (?:is|are)|need(?:\s+\w+){0,4}\s+tools?)\b',text,re.I):return None
    if re.match(r'\s*(?:please\s+)?(?:use|open|launch|check|calculate|verify)\b',text,re.I):return None
    return ('ThemHands is already connected. It is my local tool layer for Windows and network checks, '
            'protected-file verification, Calculator controls, and opening a blank Edge window. '
            'General app and file control, and navigating browser pages, are not connected yet.')


class ToolState(State):
    def execute(self,call):
        name=call.get('function',{}).get('name');args=call.get('function',{}).get('arguments',{})
        if name not in {'open_browser_window','get_tool_capabilities'}:return super().execute(call)
        if not isinstance(args,dict) or args:raise ValueError('This tool takes no arguments')
        self.check_stop()
        if name=='get_tool_capabilities':
            result={**CAPABILITIES,'target':self.chat.target}
            self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
            self.emit('observation',json.dumps(result));return result
        if self.chat.target=='other':raise ValueError('That computer is not connected. No browser was opened.')
        self.emit('tool_request',json.dumps({'name':name,'arguments':args}))
        result=open_browser(self.check_stop,self.emit)
        self.emit('observation',json.dumps(result))
        return result
