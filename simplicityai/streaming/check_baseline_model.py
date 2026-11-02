"""Opt-in local-model diagnostic selection; all observations are synthetic."""
import json
import server

CASES=[
 ('Check the free space on my drives and whether storage needs attention. Do not change anything.',{'storage'}),
 ('Check Device Manager for problems and inspect my wireless adapter driver. Do not install anything.',{'devices','drivers'}),
 ('This Windows restarted unexpectedly. Review recent error events and explain what they establish. Do not repair anything.',{'events'}),
 ('Check whether any automatic services are stopped. Do not start or stop anything.',{'services'}),
 ('Can you check this Windows for startup problems and whether boot configuration can be read? Do not repair anything.',{'startup'}),
 ('Check my current BitLocker, TPM and Secure Boot status. Keep unavailable checks unknown.',{'security'}),
 ('Check the recorded Windows updates and recent update failures, without installing or scanning for updates.',{'updates'})]


def run():
    reports=[]
    for prompt,expected in CASES:
        areas=[];spoken=[];agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
        def execute(call):
            name=call['function']['name'];args=call['function'].get('arguments',{})
            if name=='inspect_windows':
                area=args['area'];areas.append(area)
                data={'system':[{'Caption':'Windows 11','FreePhysicalMemory':8000000}],
                      'storage':[{'DeviceID':'C:','SizeGB':256,'FreeGB':11,'SizeGiB':238.42,'FreeGiB':10.24,'FreePercent':4.3,'HealthStatus':'Unknown'}],
                      'devices':[{'Name':'Wireless adapter','ConfigManagerErrorCode':28}],
                      'drivers':[],
                      'events':[{'ProviderName':'SyntheticProvider','Id':123,'TimeCreatedUTC':'2026-11-01T10:00:00Z','Message':'Synthetic test event; cause not established.'}],
                      'services':[{'Name':'SyntheticService','StartMode':'Auto','State':'Stopped'}],
                      'startup':[{'Name':'Boot configuration','status':'unknown','reason':'Access denied'}],
                      'security':[{'Name':'Secure Boot','status':'unknown','reason':'Access denied'}],
                      'updates':[{'HotFixID':'SyntheticKB','InstalledOn':'2026-10-30'}]}.get(area,[])
                return {'simulation':True,'area':area,'scope':'Windows running SimplicityAI','changes_made':False,'sections':[{'name':area,'status':'available','matching_count':len(data),'data':data}], 'limitations':'Synthetic records only; no real Windows was inspected.'}
            if name=='confirm_running_windows':return {'confirmed':True,'simulation':True}
            if name=='desktop_observe':return {'simulation':True,'snapshot':'fixture','observations':'SimplicityAI foreground; no requested utility window open.'}
            if name=='open_desktop_app':return {'simulation':True,'launch_requested':True,'completion_verified':False}
            raise ValueError('Tool blocked in synthetic baseline test: '+name)
        agent.state.execute=execute
        try:
            agent.run(prompt,spoken.append)
            reply=''.join(spoken)
            accurate='storage' not in expected or ('110 GB' not in reply and '110GB' not in reply)
            reports.append({'expected':sorted(expected),'selected':areas,'passed':expected<=set(areas) and accurate,'reply':reply})
        except Exception as error:reports.append({'expected':sorted(expected),'selected':areas,'passed':False,'error':str(error),'drafts':[m.get('content') for m in agent.state.messages if m.get('role')=='assistant' and m.get('content')]})
        finally:agent.state.close()
    print(json.dumps({'simulation_only':True,'cases':reports},ensure_ascii=True))
    if not all(case['passed'] for case in reports):raise SystemExit(1)


if __name__=='__main__':run()
