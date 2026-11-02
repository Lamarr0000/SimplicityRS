"""Detect actionable desktop requests and reject permission-only/planning drafts."""
import re


def desktop_request(text):
    return bool(re.search(r'\b(open|launch|close|minimize|minimise|navigate|search|create|click|type|save|write)\b',text,re.I)
                and re.search(r'\b(browser|edge|google|goog el|googel|desktop|document|notepad|explorer|copilot|(?:task|device)\s*(?:manager|major)|disk\s*management|event\s*viewer|settings|app|file|web\s*page)\b',text,re.I))


def requested_app(text):
    if not re.search(r'\b(open|launch|I meant)\b',text,re.I):return None
    if re.search(r"\b(?:do not|don't|never)\s+(?:open|launch)\b",text,re.I):return None
    for name in ['device_manager','disk_management','event_viewer','task_manager','system_information','reliability_monitor','notepad','explorer','calculator','settings']:
        if re.search(r'\b'+name.replace('_',r'\s*')+r'\b',text,re.I):return name
    # High-confidence spelling variation over registered two-word utilities.
    # Original recognized text remains unchanged in the transcript.
    from difflib import SequenceMatcher
    words=re.findall(r'[a-z]+',text.lower());scores=[]
    for name in ['device_manager','disk_management','event_viewer','task_manager','system_information','reliability_monitor']:
        score=max((SequenceMatcher(None,' '.join(words[i:i+2]),name.replace('_',' ')).ratio() for i in range(len(words)-1)),default=0)
        scores.append((score,name))
    scores.sort(reverse=True)
    if scores[0][0]>=.88 and scores[0][0]-scores[1][0]>=.1:return scores[0][1]
    return None


def unfinished_draft(text):
    if re.search(r"\b(?:let me (?:first )?(?:confirm|try|attempt|ensure|wait)|I (?:can|will|'ll) (?:attempt|try|wait)|keep you updated|let you know when|provide.{0,60}once.{0,20}ready)\b",text,re.I):return True
    if re.search(r"\b(?:I (?:cannot|can't|do not|don't) (?:directly )?(?:open|create|interact)|I (?:do not|don't) have the (?:capability|ability))\b",text,re.I):return True
    if re.search(r'\b(would you like|shall I|should I|may I|can I proceed|let me (?:proceed|start|check|type|open|search|click|navigate)|I\s*(?:will|\x27ll)\s+(?:open|type|search|click|navigate|proceed|check))\b',text,re.I):return True
    return bool(re.search(r'\b(could|can) you\b.{0,90}\b(where|locate|search (?:box|bar)|control|element)\b',text,re.I))


def search_result_observed(text):
    # Require an observed search destination, not a launch/typing promise.
    if re.search(r'/sorry/|unusual traffic|verify.{0,15}(?:human|robot)',text,re.I):return False
    return bool(re.search(r'https?://[^\s"<>\\]+(?:[?&](?:q|query|search_query)=|/search\?)',text,re.I))


def web_search_request(text):
    if re.search(r"\b(?:don't|do not|never)\s+(?:do a |perform a )?search\b",text,re.I):return None
    if not re.search(r'\b(?:can you|could you|please|open|do a search)\b|^\s*search\b',text,re.I):return None
    named=re.search(r'\b(?:google|goggle|googel|googal)\s+search(?:\s+for)?\s+(.+)',text,re.I)
    match=re.search(r'\bsearch(?:\s+(?:on\s+)?(?:google|googal|googel))?\s+for\s+(.+)',text,re.I) or named
    if not match:return None
    query=re.sub(r'\s+(?:(?:on\s+)?(?:google|googal|googel)\s*(?:search)?\s*)?(?:please)?[.!?]*\s*$','',match[1],flags=re.I).strip(' \"\'.!?')
    return query if 0<len(query)<=300 else None


CONTINUE=('The user has already authorized this ordinary desktop task. Do not ask permission to open, '
          'observe, click, type or submit the requested web search. A web search is not sending a message '
          'to another person. Use browser_observe for owned web pages and desktop_observe for native apps to locate controls; never ask the user for '
          'control IDs or locations you can inspect. Continue the ENTIRE original task using tools now. '
          'Do not finish with a promise to act. Finish only with actual observed results or a concrete '
          'tool failure/blocker. User takeover, Stop and unavailable tools still stop work. Consequential '
          'recovery/disk/security operations remain outside this ordinary-task authorization.')
