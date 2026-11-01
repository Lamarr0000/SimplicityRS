"""Synthetic model/tool-selection benchmark. Never executes requested tools."""
import json
from pathlib import Path
import time
import urllib.request
from conversation import CHAT_SYSTEM,CHAT_TOOLS

CASES=[
 ('greeting','Good morning. This is a voice test.','unknown'),
 ('clarification','My computer sometimes freezes. What should we check first?','unknown'),
 ('calculator','Use Calculator to multiply twelve by eight.','unknown'),
 ('network','Run the read-only network check in this VM.','current'),
 ('outside_target','Open Calculator on the physical host outside this VM.','other'),
 ('uncertain_dns','A DNS query timed out. Does that prove the internet is broken?','unknown'),
]


def run(model,name,prompt,target):
    scope='Current diagnostic target: '+{'unknown':'unknown; ask before diagnostics.','current':'running Windows explicitly confirmed.','other':'another computer, not connected to these tools.'}[target]
    payload={'model':model,'messages':[{'role':'system','content':CHAT_SYSTEM+'\n'+scope},{'role':'user','content':prompt}],'tools':CHAT_TOOLS,'stream':True,'keep_alive':'15m','options':{'num_ctx':8192,'num_predict':220,'temperature':0}}
    if model=='gpt-oss:20b':payload['think']='low'
    request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    start=time.monotonic();first=None;content='';calls=[];final={}
    with urllib.request.urlopen(request,timeout=180) as response:
        for line in response:
            item=json.loads(line)
            if item.get('error'):raise RuntimeError(item['error'])
            message=item.get('message',{})
            if (message.get('content') or message.get('tool_calls')) and first is None:first=time.monotonic()-start
            content+=message.get('content','');calls.extend(message.get('tool_calls',[]))
            if item.get('done'):final=item
    return {'model':model,'case':name,'first_output_seconds':round(first or 0,2),'elapsed_seconds':round(time.monotonic()-start,2),'reply':content,'tool_calls':calls,'done_reason':final.get('done_reason'),'metrics':{k:final.get(k) for k in ['prompt_eval_count','prompt_eval_duration','eval_count','eval_duration','load_duration']}}


def main():
    results=[]
    for model in ['granite4:3b','gpt-oss:20b']:
        for case in (CASES if model=='granite4:3b' else CASES[:2]):
            result=run(model,*case);results.append(result);print(json.dumps(result),flush=True)
    folder=Path('C:/SimplicityAI-Lab/ThemHands/logs')
    (folder/'model-latency-comparison.json').write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':main()
