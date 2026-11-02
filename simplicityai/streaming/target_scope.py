"""Current-Windows binding tolerates narrow app-name speech spellings.

This resolves scope only. Original recognized words remain in chat/evidence.
Bare yes never selects between the current Windows and another computer.
"""
import re
from conversation import Conversation

OTHER=re.compile(r'\b(host|(?:another|different|other) (?:windows|computer|pc|machine|vm|installation)|outside (?:this|the) vm|not this vm|not (?:the )?current windows|not (?:the )?windows (?:that (?:is|s) |as |is )?running)\b',re.I)
OTHER=re.compile(OTHER.pattern+r'|\bnot (?:this |the |current )?(?:windows(?: installation)?|computer)\b',re.I)
CURRENT=re.compile(r"\b(?:windows(?:\s+installation)?|computer)\s+(?:(?:that\s+(?:is\s+)?|that['’]s\s+|as\s+|is\s+))?running\s+simplicity\s*(?:a\s*i|ai|ay)\b",re.I)


class TargetConversation(Conversation):
    def begin(self,text):
        if re.search(r'\brecovery\b.{0,35}\b(?:image|environment|usb|media)\b',text,re.I) and re.search(r'\bboot',text,re.I):
            self.target='other';self.offline_target=True
        if OTHER.search(text):self.target='other'
        messages,start=super().begin(text)
        if re.match(r'\s*(?:hey|hello|hi|good (?:morning|afternoon|evening))\b',self.original_issue,re.I) and not re.search(r'not (?:start|work)|crash|slow|error|driver|boot|out of space|fail',self.original_issue,re.I):self.original_issue=''
        if getattr(self,'offline_target',False):messages[0]['content']+='\nThe user describes booting recovery media to help an unbootable Windows installation. That affected installation is not connected to the current-Windows collectors. Do not recommend current SFC/driver checks as diagnosis of that installation. Explain the distinction and ask what boot failure screen or message appeared; do not claim you have inspected offline Windows. Local desktop apps can still be opened in this recovery environment.'
        return messages,start

    def confirm(self):
        explicit_local=CURRENT.search(self.current_user) or re.search(r'\b(this vm|inside the vm|this virtual machine|current windows)\b',self.current_user,re.I)
        if not getattr(self,'offline_target',False) and re.search(r'\bthis computer\b',self.current_user,re.I):explicit_local=True
        if getattr(self,'offline_target',False) and not explicit_local:raise ValueError('The affected offline Windows is not connected')
        if explicit_local:self.offline_target=False
        if OTHER.search(self.current_user):
            raise ValueError('Another or explicitly excluded Windows target is not connected. No local diagnostic was authorized.')
        if explicit_local:
            self.offline_target=False
            self.target='current'
            return {'target':'running Windows only','confirmed':True,'offline_or_host_inspection':False}
        return super().confirm()
