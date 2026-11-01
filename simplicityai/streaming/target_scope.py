"""Current-Windows binding tolerates narrow app-name speech spellings.

This resolves scope only. Original recognized words remain in chat/evidence.
Bare yes never selects between the current Windows and another computer.
"""
import re
from conversation import Conversation

OTHER=re.compile(r'\b(host|another windows|another computer|different computer|other installation|outside (?:this|the) vm|not this vm|not (?:the )?current windows|not (?:the )?windows (?:that (?:is|s) |as |is )?running)\b',re.I)
CURRENT=re.compile(r'\bwindows\s+(?:(?:that\s+(?:is\s+)?|as\s+|is\s+))?running\s+simplicity\s*(?:a\s*i|ai|ay)\b',re.I)


class TargetConversation(Conversation):
    def begin(self,text):
        if OTHER.search(text):self.target='other'
        return super().begin(text)

    def confirm(self):
        if OTHER.search(self.current_user):
            raise ValueError('Another or explicitly excluded Windows target is not connected. No local diagnostic was authorized.')
        if CURRENT.search(self.current_user):
            self.target='current'
            return {'target':'running Windows only','confirmed':True,'offline_or_host_inspection':False}
        return super().confirm()
