"""Detect actionable desktop requests and reject permission-only/planning drafts."""
import re


def desktop_request(text):
    return bool(re.search(r'\b(open|launch|navigate|search|create|click|type|save|write)\b',text,re.I)
                and re.search(r'\b(browser|edge|google|goog el|googel|desktop|document|notepad|explorer|copilot|(?:task|device)\s*(?:manager|major)|disk\s*management|event\s*viewer|settings|app|file|web\s*page)\b',text,re.I))


def requested_app(text):
    if not re.search(r'\b(open|launch|I meant)\b',text,re.I):return None
    if re.search(r"\b(?:do not|don't|never)\s+(?:open|launch)\b",text,re.I):return None
    for name in ['device_manager','disk_management','event_viewer','task_manager','system_information','reliability_monitor','notepad','explorer','calculator','settings']:
        if re.search(r'\b'+name.replace('_',r'\s*')+r'\b',text,re.I):return name
    return None


def unfinished_draft(text):
    if re.search(r"\b(?:I (?:cannot|can't|do not|don't) (?:directly )?(?:open|create|interact)|I (?:do not|don't) have the (?:capability|ability))\b",text,re.I):return True
    if re.search(r'\b(would you like|shall I|should I|may I|can I proceed|let me (?:proceed|start|check|type|open|search|click|navigate)|I\s*(?:will|\x27ll)\s+(?:open|type|search|click|navigate|proceed|check))\b',text,re.I):return True
    return bool(re.search(r'\b(could|can) you\b.{0,90}\b(where|locate|search (?:box|bar)|control|element)\b',text,re.I))


def search_result_observed(text):
    # Require an observed search destination, not a launch/typing promise.
    return bool(re.search(r'https?://[^\s"<>\\]+(?:[?&](?:q|query|search_query)=|/search\?)',text,re.I))


def web_search_request(text):
    if re.search(r"\b(?:don't|do not|never)\s+(?:do a |perform a )?search\b",text,re.I):return None
    if not re.search(r'\b(?:can you|could you|please|open|do a search)\b|^\s*search\b',text,re.I):return None
    match=re.search(r'\bsearch(?:\s+(?:on\s+)?(?:google|googal|googel))?\s+for\s+(.+)',text,re.I)
    if not match:return None
    query=re.sub(r'\s+(?:(?:on\s+)?(?:google|googal|googel)\s*(?:search)?\s*)?(?:please)?[.!?]*\s*$','',match[1],flags=re.I).strip(' \"\'.!?')
    return query if 0<len(query)<=300 else None


CONTINUE=('The user has already authorized this ordinary desktop task. Do not ask permission to open, '
          'observe, click, type or submit the requested web search. A web search is not sending a message '
          'to another person. Use desktop_observe yourself to locate controls; never ask the user for '
          'control IDs or locations you can inspect. Continue the ENTIRE original task using tools now. '
          'Do not finish with a promise to act. Finish only with actual observed results or a concrete '
          'tool failure/blocker. User takeover, Stop and unavailable tools still stop work. Consequential '
          'recovery/disk/security operations remain outside this ordinary-task authorization.')
