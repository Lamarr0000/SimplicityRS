"""Multi-turn replay of reported failures. Every OS result is simulated."""
import json
from unittest.mock import patch
import server
from intent_control import repeated_target_question

PROMPTS=[
 'My computer is not starting up correctly.',
 'For this exercise I mean this computer.',
 "Yes, I am referring to the Windows installation that is running Simplicity A I.",
 "Just run a diagnostic on the computer that's running Simplicity A I.",
 'Never mind, forget it.',
 'Open a web browser and go to fast.com.',
 'Close the Fast browser please.',
 'Minimise everything open except yourself.',
 'Open Calculator and execute one plus one. Tell me the results.'
]


def run():
    reports=[];calls=[];agent=server.Agent(lambda *a,**kw:None,'qwen3:8b');original=agent.state.execute
    def desktop(name,args,check_stop):
        if name=='list_windows':return {'simulation':True,'windows':[{'id':'browser','title':'Fast.com - Microsoft Edge','process':'msedge.exe','assistant_window':False},{'id':'assistant','title':'SimplicityAI','process':'SimplicityAI.exe','assistant_window':True}]}
        if name=='manage_window':return {'simulation':True,'all_verified':True,'action':args['action']}
        if name=='open_desktop_app':return {'simulation':True,'launch_requested':True,'completion_verified':False}
        if name=='desktop_observe':return {'simulation':True,'snapshot':'fixture','observations':'Fast.com - Microsoft Edge foreground; address https://fast.com/ . Internet speed test page visible.'}
        raise ValueError('Unsupported action blocked during replay: '+name)
    def collect(area,query,check_stop):
        data={'storage':[{'DeviceID':'C:','FreeGiB':90,'SizeGiB':128,'FreePercent':70.3}],
              'system':[{'Caption':'Windows 11','FreePhysicalMemory':8000000}],
              'devices':[{'Name':'Synthetic device','ConfigManagerErrorCode':0}],
              'events':[{'ProviderName':'SyntheticProvider','Id':1,'Message':'Example event; cause not established.'}],
              'startup':[]}.get(area,[])
        return {'simulation':True,'area':area,'scope':'running Windows only','sections':[{'name':area,'status':'available','returned_count':len(data),'data':data}],'changes_made':False}
    def execute(call):
        name=call['function']['name'];calls.append(name)
        if name=='calculate_in_calculator':return {'simulation':True,'display':'2','final_display_reread':True}
        if name in {'get_health_snapshot','get_network_snapshot'}:raise ValueError('Use the already collected focused evidence in this replay')
        return original(call)
    agent.state.execute=execute;agent.state.desktop.execute=desktop
    try:
        with patch('tool_state.inspect_windows',side_effect=collect):
            for prompt in PROMPTS:
                before=len(calls);spoken=[]
                try:
                    agent.run(prompt,spoken.append);reply=''.join(spoken)
                    selected=calls[before:]
                    passed=not (agent.state.chat.target=='current' and repeated_target_question(reply))
                    if 'Never mind' in prompt:passed=passed and not selected
                    if prompt.startswith('Close') or prompt.startswith('Minimise'):passed=passed and 'manage_window' in selected
                    if prompt.startswith('Open Calculator'):passed=passed and selected==['calculate_in_calculator'] and '2' in reply
                    reports.append({'prompt':prompt,'selected':selected,'target':agent.state.chat.target,'passed':passed,'reply':reply})
                except Exception as error:reports.append({'prompt':prompt,'passed':False,'error':str(error),'selected':calls[before:]})
    finally:agent.state.close()
    print(json.dumps({'simulation_only':True,'cases':reports},ensure_ascii=True))
    if not all(row['passed'] for row in reports):raise SystemExit(1)


if __name__=='__main__':run()
