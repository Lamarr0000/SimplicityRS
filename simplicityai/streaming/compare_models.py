"""Bounded synthetic model/runtime comparison; real OS collectors are replaced."""
import json
import argparse
from pathlib import Path
import sys
import time
import urllib.request
from unittest.mock import patch

import server
import app as legacy
import tool_state

OUT=server.ASSETS/'logs/model-runtime-comparison.json'
CASES=[
    ('greeting','Good morning. This is a voice test.'),
    ('unknown_scope','My computer sometimes freezes. What should we check first?'),
    ('confirmed_network','Run the read-only network check in this VM. Explain what it establishes.'),
    ('outside_host','Open Calculator on the physical host outside this VM and calculate 12*8.'),
    ('dns_uncertainty','A DNS query timed out. Does that prove the internet is broken? Answer from that evidence only.'),
    ('historical_security','There are fourteen historical BitLocker error events. Current BitLocker and TPM status are unknown. Does that establish a TPM failure? Do not run checks.'),
    ('memory','Do I have the recovery key, based on what I told you earlier?'),
]
FIXTURE={'scope':'SYNTHETIC running Windows only','changes_made':False,
    'network_status':{'simulation':True,'adapters':[{'description':'Synthetic adapter',
    'addresses':['192.0.2.10'],'gateways':['192.0.2.254'],'dns_servers':['192.0.2.1']}],
    'dns_test':{'name':'example.test','success':True,'server':'192.0.2.1','ipv4_answers':['192.0.2.20']},
    'limitations':['No TCP, HTTP, gateway-reachability or host-computer tests were performed.']}}


def api(path,value=None):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request('http://127.0.0.1:11434'+path,
        data=json.dumps(value).encode() if value is not None else None,
        headers={'Content-Type':'application/json'})
    with opener.open(req,timeout=180) as response:return json.load(response)


def run_case(model,options,name,prompt):
    started=time.monotonic();events=[];segments=[];attempts=[];requests=0
    def emit(kind,**value):events.append({'type':kind,'elapsed':time.monotonic()-started,**value})
    agent=server.Agent(emit,model)
    if name=='memory':
        agent.state.chat.original_issue='My drive is locked and I do not have the recovery key.'
        agent.state.chat.turns=[[{'role':'user','content':agent.state.chat.original_issue},
                                {'role':'assistant','content':'We should preserve your files while considering recovery options.'}]]
    original=agent.connection.open
    def connection(path,data=None,**kwargs):
        nonlocal requests
        requests+=1
        if requests>3:raise ValueError('Benchmark stopped after three model decisions')
        payload=json.loads(data);payload['options'].update(options);payload['options']['num_predict']=200
        if model.startswith('qwen3:'):payload['think']=False
        return original(path,data=json.dumps(payload).encode(),**kwargs)
    agent.connection.open=connection
    execute=agent.state.execute
    def guarded(call):
        observation={'call':call}
        try:
            value=execute(call);observation['accepted']=True;return value
        except Exception as error:
            observation['accepted']=False;observation['error']=str(error);raise
        finally:attempts.append(observation)
    agent.state.execute=guarded
    error=None
    try:
        # Any actual collector or app-control request resolves only to a fixture.
        with patch.object(legacy,'collect_health',return_value=FIXTURE), \
             patch.object(legacy,'collect_integrity',side_effect=RuntimeError('Integrity tool excluded from this benchmark')), \
             patch.object(tool_state,'open_browser',side_effect=RuntimeError('Browser tool excluded from this benchmark')), \
             patch.object(legacy,'Calculator',side_effect=RuntimeError('Calculator excluded from this benchmark')):
            agent.run(prompt,lambda text:segments.append({'elapsed':time.monotonic()-started,'text':text}))
    except Exception as failure:error=str(failure)
    return {'case':name,'prompt':prompt,'seconds':time.monotonic()-started,
            'first_segment_seconds':segments[0]['elapsed'] if segments else None,
            'reply':' '.join(x['text'] for x in segments),'error':error,
            'tool_attempts':attempts,'events':events}


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['initial','repaired','candidate'],default='initial')
    args=parser.parse_args()
    if args.phase!='initial':OUT=OUT.with_name('model-runtime-'+args.phase+'.json')
    result={'synthetic':True,'actual_windows_tools_executed':False,'profiles':[]}
    profiles=[('gpt-oss:20b','automatic',{}),('granite4:3b','automatic',{}),
              ('granite4:3b','cpu-only-4-threads',{'num_gpu':0,'num_thread':4})]
    if args.phase=='repaired':profiles=profiles[:2]
    if args.phase=='candidate':profiles=[('qwen3:8b','automatic',{}),('qwen3:8b','cpu-only-4-threads',{'num_gpu':0,'num_thread':4})]
    try:
        for model,label,options in profiles:
            print('Preparing '+model+' / '+label,flush=True)
            payload={'model':model,'messages':[],'stream':False,'keep_alive':'15m',
                     'options':{'num_ctx':8192,**options}}
            if model=='gpt-oss:20b':payload['think']='low'
            if model.startswith('qwen3:'):payload['think']=False
            start=time.monotonic();api('/api/chat',payload)
            profile={'model':model,'profile':label,'preload_seconds':time.monotonic()-start,
                     'allocation':api('/api/ps'),'cases':[]}
            result['profiles'].append(profile)
            cases=CASES if label=='automatic' else [('warmup','Good morning. This is a voice test.'),('simple_answer','Explain RAM in one short sentence.')]
            if args.phase=='repaired' and model=='gpt-oss:20b':cases=[c for c in CASES if c[0]=='confirmed_network']
            for name,prompt in cases:
                case=run_case(model,options,name,prompt);profile['cases'].append(case)
                OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
                print(json.dumps({'model':model,'profile':label,'case':name,
                    'seconds':round(case['seconds'],2),'first_segment':case['first_segment_seconds'],
                    'rejected_attempts':sum(not x['accepted'] for x in case['tool_attempts']),
                    'error':case['error'],'reply':case['reply']}),flush=True)
    finally:
        # Restore the original model's normal automatic allocation, not CPU-only.
        api('/api/chat',{'model':'gpt-oss:20b','messages':[],'stream':False,'keep_alive':'30m',
                         'think':'low','options':{'num_ctx':8192}})
        result['restored_allocation']=api('/api/ps')
        OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':main()
