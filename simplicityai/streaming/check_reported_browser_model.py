"""Opt-in exact-task local-model replay. All OS/browser results are simulated."""
import json
from pathlib import Path
from datetime import datetime
import server


def main():
    agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
    calls=[];complete=False;reports=[]
    def execute(call):
        nonlocal complete
        name=call['function']['name'];args=call['function']['arguments'];calls.append(name)
        if name=='close_app_windows':return {'simulation':True,'all_verified':True,'matched_windows':1}
        if name=='browser_open':return {'simulation':True,'opened':True,'observation_tool':'browser_observe'}
        if name=='browser_wait':complete=True
        if name in {'browser_observe','browser_wait'}:
            return {'simulation':True,'snapshot':'synthetic','url':'https://fast.com/',
                    'observations':'SIMULATED PAGE, NOT A REAL SPEED TEST. '+
                    ('Download test complete. Your Internet speed is42 Mbps.' if complete else
                     'Download measurement in progress. Current value0. No Start Test button is exposed. Wait for the asynchronous result.'),
                    'condition_met':complete}
        raise ValueError('Unsupported action blocked during simulated replay: '+name)
    agent.state.execute=execute
    prompts=['can you close my calculator app, open a browser and conduct a speed test at fast.com',
             'yes please', 'the test has been complete. please look at the screen and explain the results',
             'close all browses window but leave apps open']
    try:
        for prompt in prompts:
            before=len(calls);spoken=[]
            try:
                agent.run(prompt,spoken.append)
                text=''.join(spoken)
                passed=('open_browser_window' not in calls[before:] and 'unable to view' not in text.lower())
                if 'speed test at' in prompt:passed=passed and complete and '42' in text
                if 'explain the results' in prompt:passed=passed and calls[before:][0]=='browser_observe' and '42' in text
                reports.append({'prompt':prompt,'selected':calls[before:],'reply':text,'passed':passed})
            except Exception as error:reports.append({'prompt':prompt,'selected':calls[before:],'error':str(error),'passed':False})
    finally:agent.state.close()
    result={'simulation_only':True,'real_desktop_actions':False,'cases':reports}
    path=Path('C:/SimplicityAI-Lab/ControlAdapter')/('reported-browser-model-replay-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))
    if not all(row['passed'] for row in reports):raise SystemExit(1)


if __name__=='__main__':main()
