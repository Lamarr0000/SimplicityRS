"""Application-owned cancellation, continuation and basic arithmetic intent."""
import re


def cancelled(text):
    if re.match(r"^\s*(?:time(?:'s|s)?(?: is)? up|that's enough|that is enough|stop here)(?:[.! ,]|$)",text,re.I):return True
    return bool(re.search(r"\b(?:never mind|nevermind|forget it|don't (?:even )?worry about it|do not worry about it|cancel (?:that|this|it))\b",text,re.I) or re.fullmatch(r'\s*(?:stop|cancel)[.!\s]*',text,re.I))


def continuation(previous,current):
    return bool(re.search(r'\b(?:of|and|is|the|my|to|for)\s*$',previous,re.I) or
                re.match(r'\s*(?:and\b|tell me the results\b|working drivers\b)',current,re.I))


def diagnostic_request(text):
    return bool(re.search(r'run.{0,20}diagnostic|(?:do|run).{0,15}whatever.{0,65}(?:identify|determine)|help.{0,30}(?:identify|determine).{0,30}(?:problem|wrong)|\bmy (?:computer|pc).{0,25}(?:not starting|slow|freezing|crashing)',text,re.I))


def repeated_target_question(text):
    for sentence in re.split(r'[.!?\n]',text):
        if re.search(r'already confirmed|is confirmed|no further.{0,20}confirmation',sentence,re.I):continue
        if re.search(r'(?:need to|please|can you|could you|must|let me).{0,12}confirm.{0,90}(?:windows|environment|target)|are you referring to.{0,70}(?:windows|vm|simplicity)|which (?:windows|environment|vm)',sentence,re.I):return True
    return False


def window_request(text):
    if re.search(r'\bminimi[sz]e\b',text,re.I) and re.search(r'everything|all',text,re.I) and re.search(r'except|yourself|your window',text,re.I):return 'minimize_others'
    from task_agenda import close_intent
    close=close_intent(text)
    if close and close['app']=='browser':return 'close_browser'
    return None


def arithmetic(text):
    if not re.search(r'calculator|calcular|calculate|execute|press|what is|how much',text,re.I):return None
    numbers={'zero':'0','one':'1','two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9','ten':'10','eleven':'11','twelve':'12','thirteen':'13','fourteen':'14','fifteen':'15','sixteen':'16','seventeen':'17','eighteen':'18','nineteen':'19','twenty':'20'}
    value=re.sub(r'\b('+'|'.join(numbers)+r')\b',lambda match:numbers[match[0].lower()],text,flags=re.I)
    value=re.sub(r'\b(?:multiplied by|times)\b','*',value,flags=re.I)
    value=re.sub(r'\bplus\b','+',value,flags=re.I);value=re.sub(r'\bminus\b','-',value,flags=re.I)
    value=re.sub(r'\bdivided by\b','/',value,flags=re.I)
    value=re.sub(r'(?<=\d)\s*[xX]\s*(?=\d)','*',value)
    match=re.search(r'(?<!\d)(\d{1,4}(?:\.\d{1,4})?)\s*([+*/×÷-])\s*(\d{1,4}(?:\.\d{1,4})?)(?!\d)',value)
    if match and re.match(r'\s*[+*/×÷-]\s*\d',value[match.end():]):return None
    if match and re.search(r'-\s*$',value[:match.start()]):return None
    return ''.join(match.groups()) if match else None


def retry_arithmetic(text,transcript):
    if not re.search(r'\b(?:try again|retry)\b',text,re.I):return None
    from target_scope import OTHER
    count=0
    for row in reversed(transcript):
        if row.get('role')!='user' or row.get('content')==text:continue
        previous=row.get('content','');count+=1
        if count>6 or cancelled(previous) or OTHER.search(previous):return None
        expression=arithmetic(previous)
        if expression:return expression
        if re.search(r'\b(?:open|run|check|inspect|search|create|close)\b',previous,re.I):return None
    return None


def exit_request(text):
    # Limited polite prefixes, never arbitrary text before an exit-shaped fragment.
    prefix=r"\s*(?:(?:yes|yeah|ye|a|m|um|uh|okay|ok|well|hey)[,\s]+){0,4}(?:(?:can|could|would) you\s+)?(?:please\s+)?"
    command=r"(?:close yourself|exit yourself|shut yourself down|turn yourself off|switch yourself off|(?:close|exit|quit) (?:simplicity\s*ai|this app|the app))"
    return bool(re.fullmatch(prefix+command+r"(?:\s+(?:please|now)){0,2}[.!?\s]*",text,re.I))
