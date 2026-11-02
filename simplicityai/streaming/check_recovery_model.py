"""Local-model replay of recovery scope and viewer requests; no real OS actions."""
import json
from unittest.mock import patch
import server


def run():
    reports=[];agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
    def desktop(name,args,check_stop):
        if name=='open_desktop_app':return {'simulation':True,'launch_requested':True,'completion_verified':False}
        if name=='desktop_observe':return {'simulation':True,'snapshot':'fixture','observations':'Device Manager is the foreground window. Device tree visible.'}
        raise ValueError('No other desktop actions permitted in replay')
    agent.state.desktop.execute=desktop
    try:
        with patch('tool_state.inspect_windows',side_effect=AssertionError('Offline Windows must not trigger a current collector')) as collect:
            for prompt in [
                'My Windows never reaches the start menu. I booted from a recovery image to access you.',
                'Help me determine what is wrong with that Windows. Can you check its drivers?',
                'Open Device Manager in this recovery environment so I can see it.']:
                spoken=[]
                try:
                    agent.run(prompt,spoken.append)
                    reports.append({'target':agent.state.chat.target,'reply':''.join(spoken),'current_collectors_called':collect.call_count,'passed':agent.state.chat.target=='other' and collect.call_count==0})
                except Exception as error:reports.append({'passed':False,'error':str(error)})
    finally:agent.state.close()
    print(json.dumps({'simulation_only':True,'cases':reports},ensure_ascii=True))
    if not all(case['passed'] for case in reports):raise SystemExit(1)


if __name__=='__main__':run()
