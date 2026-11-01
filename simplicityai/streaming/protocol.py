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
