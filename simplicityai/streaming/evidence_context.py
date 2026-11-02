"""Bound diagnostic context without altering the full local evidence log."""
import copy
import json


def model_evidence(result,limit=6000):
    if not isinstance(result,dict) or 'sections' not in result:return json.dumps(result)
    value=copy.deepcopy(result)
    while len(json.dumps(value))>limit:
        candidates=[section for section in value['sections'] if len(section.get('data',[]))>1]
        if not candidates:break
        section=max(candidates,key=lambda item:len(json.dumps(item['data'])))
        section['data'].pop();section['model_context_truncated']=True
        section['model_visible_rows']=len(section['data'])
    return json.dumps(value)


def model_messages(messages,start,budget=20000):
    """Keep the current task and newest complete prior exchanges within budget."""
    current=copy.deepcopy(messages[start:]);system=messages[:1]
    size=lambda values:len(json.dumps(values))
    # Current task receipts stay paired; compact older observations rather than
    # silently dropping the user's request or an entire evidence category.
    for message in current[:-1]:
        if size(system+current)<=budget:break
        if message.get('role')=='tool':
            try:message['content']=model_evidence(json.loads(message['content']),1200)
            except (ValueError,TypeError):pass
    groups=[]
    for message in copy.deepcopy(messages[1:start]):
        if message.get('role')=='tool':
            try:message['content']=model_evidence(json.loads(message['content']),1200)
            except (ValueError,TypeError):pass
        if message.get('role')=='user' or not groups:groups.append([])
        groups[-1].append(message)
    selected=[]
    for group in reversed(groups):
        if size(system+group+selected+current)>budget:break
        selected=group+selected
    return system+selected+current
