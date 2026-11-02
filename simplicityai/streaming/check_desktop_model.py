"""Opt-in local model routing check with simulated results; NO desktop actions."""
import json
import server


def run():
    cases=[('Open Microsoft Edge and navigate to https://www.google.com. Verify whether the page loaded.',
            {'open_desktop_app','desktop_observe'}),
           ('Create a new text document on my desktop named Simplicity Test.txt containing Hello from SimplicityAI.',
            {'create_desktop_text'}),
           ('What can the Lazesoft tools in the Simplicity launcher do? Do not run them.',
            {'get_recovery_tool_catalog'})]
    reports=[]
    for prompt,expected in cases:
        calls=[];chunks=[];agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
        original=agent.state.execute
        def simulated(call):
            name=call['function']['name'];calls.append(name)
            if name=='open_desktop_app':return {'simulation':True,'launch_requested':True,'completion_verified':False,'next':'Observe actual page'}
            if name=='desktop_observe':return {'simulation':True,'snapshot':'fixture','observations':'Microsoft Edge foreground. Address and search bar: https://www.google.com/ . Page heading: Google. Search field visible.'}
            if name=='create_desktop_text':return {'simulation':True,'created':True,'content_verified':True,'path':'SIMULATED Desktop/Simplicity Test.txt'}
            if name=='get_recovery_tool_catalog':return original(call)
            raise ValueError('Unexpected tool blocked in synthetic test: '+name)
        agent.state.execute=simulated
        try:
            agent.run(prompt,chunks.append)
            reply=''.join(chunks)
            labelled=not (expected & {'open_desktop_app','create_desktop_text'}) or 'simulat' in reply.lower()
            reports.append({'expected':sorted(expected),'called':calls,'passed':expected<=set(calls) and labelled,'reply':reply})
        finally:agent.state.close()
    print(json.dumps({'simulation_only':True,'cases':reports},ensure_ascii=True))
    if not all(report['passed'] for report in reports):raise SystemExit(1)


if __name__=='__main__':run()
