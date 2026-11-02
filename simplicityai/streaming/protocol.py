"""Bounded progressive natural-language segments; no model reasoning."""
import re


class Segments:
    def __init__(self):self.prefix='';self.released=0

    def feed(self,prefix,final=False):
        if len(prefix)>4000 or not prefix.startswith(self.prefix):raise ValueError('Reply stream changed or exceeded its bound')
        self.prefix=prefix;result=[]
        while self.released<len(prefix):
            remaining=prefix[self.released:];limit=80 if not self.released else 160
            boundary=re.search(r'[.!?](?:\s|$)',remaining[:limit+1])
            end=boundary.start()+1 if boundary and (final or boundary.end()<len(remaining) or remaining[boundary.end()-1].isspace()) else None
            if end is None and len(remaining)>limit:
                end=remaining[:limit+1].rfind(' ')
                if end<1:raise ValueError('Unbroken reply segment too long')
            if end is None:
                if not final:break
                end=len(remaining)
            result.append(remaining[:end]);self.released+=end
            while self.released<len(prefix) and prefix[self.released].isspace():self.released+=1
        return result


def internal_output(text,control_task=False):
    """Recognize leaked tool protocol/desktop trees, not arbitrary user code."""
    patterns=[r'\[\s*(?:control\s+\d+|action\s*:)',
              r'<\|(?:im_start|im_end|tool_call|python_tag)',
              r'</?(?:tool_call|function_call|think)>',
              r'["\'](?:tool_calls|function_call)["\']\s*:',
              r'["\']function["\']\s*:\s*\{',
              r'\b(?:Action|Thought)\s*:\s*(?:click\(|type\(|finished\(|I )',
              r'\b(?:desktop_interact|desktop_click_control|browser_act|open_desktop_app)\s*\(']
    return any(re.search(pattern,text,re.I) for pattern in patterns) or bool(control_task and '```' in text)
