"""Bound diagnostic context without altering the full local evidence log."""
import copy
import json


def model_evidence(result,limit=6000):
    if isinstance(result,dict) and 'findings' in result:
        records=result['findings'];value={**result,'findings':[json.loads(model_evidence(item,max(800,limit//max(1,len(records))))) for item in records]}
        return json.dumps(value)
    if not isinstance(result,dict):return json.dumps(result)
    if 'sections' not in result:
        value=copy.deepcopy(result)
        if 'observations' not in value:return json.dumps(value)
        while len(json.dumps(value))>limit:
            value['model_context_truncated']=True
            fields=[key for key in ('observations','visible_text') if isinstance(value.get(key),str) and len(value[key])>80]
            if fields:
                key=max(fields,key=lambda key:len(value[key]));text=value[key]
                size=max(10,len(text)//4)
                value[key]=text[:size]+'\n[... omitted ...]\n'+text[-size:]
            elif len(value.get('structured_controls',[]))>1:
                value['structured_controls'].pop()
            else:break
        return json.dumps(value)
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
