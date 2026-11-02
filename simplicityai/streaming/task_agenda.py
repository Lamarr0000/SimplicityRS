"""Bounded ordinary-task continuity. Raw user wording remains in the transcript."""
import re

CLOSE=re.compile(r"\bclose\s+(?:(?:all|the|my|open|these|those|your|any)\s+)*(calculator(?:\s+app)?|(?:fast\s+)?(?:browsers?|browses))(?:\s+windows?)?\b",re.I)
FOLLOW=re.compile(r"^\s*(?:yes(?: please)?|please|proceed|continue|do it|ok(?:ay)?(?: go)?|go(?: ahead)?|use edge)[.!\s]*$",re.I)


def close_intent(text):
    match=CLOSE.search(text)
    if not match or re.search(r"\b(?:don't|do not|never)\s+close\b",text,re.I):return None
    result={'app':'calculator' if match[1].lower().startswith('calculator') else 'browser',
            'all':bool(re.search(r'\ball\b',match[0],re.I))}
    if match[1].lower().startswith('fast '):result['title_contains']='fast'
    return result


def requested_url(text):
    if re.search(r"\b(?:don't|do not|never)\s+(?:open|navigate|visit)\b",text,re.I):return None
    match=re.search(r'https://[^\s<>\"]+|\b(?:[a-z0-9-]+\.)+(?:com|org|net|gov|edu|io)(?:/[^\s<>\"]*)?',text,re.I)
    if not match:return None
    value=match[0].rstrip('.,!?;')
    return value if value.lower().startswith('https://') else 'https://'+value


def conversation_export_request(text):
    if re.search(r"\b(?:don't|do not|never)\s+(?:save|export|copy|create)\b",text,re.I):return False
    return bool(re.search(r'\b(?:conversation|session|chat(?:\s*session|cession)?)\b',text,re.I)
                and re.search(r'\b(?:document|file|export|save|copy)\b',text,re.I))


def driver_backup_request(text):
    return bool(re.search(r'\bdrivers?\b',text,re.I) and re.search(r'\b(?:back\s*up|backup|copy|export)\b',text,re.I)
                and not re.search(r"\b(?:don't|do not|never)\s+(?:back\s*up|copy|export)\b",text,re.I))

DRIVER_BACKUP_LIMIT=('Driver-package backup is not connected in this build; no driver backup files were created. '
                     'Device Manager and SFC do not back up driver packages. I have not selected or run a third-party backup tool.')


def export_filename(text):
    match=re.search(r'\b(?:name it|named|call it|(?:with )?(?:the )?name)\s+(.{1,95})$',text,re.I)
    if not match:match=re.search(r'\b(?:desktop|des\s*top|destap)\s+as\s+(.{1,95})$',text,re.I)
    if not match:return None
    value=re.sub(r'\s+please[.!?]*$','',match[1],flags=re.I).strip(' .!?\"')
    return value if value.lower().endswith('.txt') else value+'.txt'


class TaskAgenda:
    def __init__(self):self.clear()
    def clear(self):
        self.original='';self.url=None;self.opened=False;self.close_done=False
    def begin(self,text):
        url=requested_url(text)
        if url and re.search(r'\b(?:open|navigate|visit|conduct|run|go to|do (?:a |the )?(?:speed )?test)\b',text,re.I):
            self.original=text;self.url=url;self.opened=False;self.close_done=False
        elif self.original and re.search(r'\b(?:instead|new task|forget (?:it|that)|never mind)\b',text,re.I):self.clear()
    def related(self,text):
        if not self.url:return False
        if re.search(r'\b(?:export|save|copy|document|chat|conversation|word|bottom)\b',text,re.I):return False
        if close_intent(text) and not requested_url(text):return False
        return (text==self.original or bool(FOLLOW.fullmatch(text)) or bool(re.match(r'^(?:yes|ok(?:ay)?|proceed|continue|do it)\b',text,re.I))
                or bool(re.search(r'\b(?:results?|speed|test|browser|page|screen|retry|again|complete|consecutively|next steps|nothing happened|do all|permission|authority|stuck)\b',text,re.I)))
    def retry(self,text):return bool(re.search(r'\b(?:try again|retry|reopen|page timed out)\b',text,re.I))
