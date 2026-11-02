"""Opt-in local model routing check with simulated results; NO desktop actions."""
import json
import server


def run():
    cases=[('Open Microsoft Edge and navigate to https://www.google.com. Verify whether the page loaded.',
            {'open_desktop_app','desktop_observe'}),
           ('Create a new text document on my desktop named Simplicity Test.txt containing Hello from SimplicityAI.',
            {'create_desktop_text'}),
           ('What can the Lazesoft tools in the Simplicity launcher do? Do not run them.',
            {'get_recovery_tool_catalog'}),
           ('HEY CAN YOU OPEN UP A WET BROWSER FOR ME AND NAVIGATE THE GOOGEL AND SEARCH FOR COMPUTER SPEE TEST',
            {'open_desktop_app','desktop_observe','desktop_interact'}),
           ('NO I SAID CAN YOU OPEN THE TASK MANAGER AND FIND OUT WHICH PROCESS IS THE MOST SEA P U INTENSIVE',
            {'open_desktop_app','desktop_observe','get_cpu_process_snapshot'})]
    reports=[]
    for prompt,expected in cases:
        calls=[];chunks=[];submitted=[];typed=[];arguments=[];active=[];agent=server.Agent(lambda *a,**kw:None,'qwen3:8b')
        original=agent.state.execute
        def simulated(call):
            name=call['function']['name'];calls.append(name)
            if name=='open_desktop_app':
                active.append(call['function']['arguments']['app'])
                return {'simulation':True,'launch_requested':True,'completion_verified':False,'next':'Observe actual window'}
            if name=='get_cpu_process_snapshot':return {'simulation':True,'sample_seconds':1.01,'highest_sampled_process':{'pid':123,'name':'BusyTest.exe','cpu_percent_of_machine':27.4},'top_processes':[{'pid':123,'name':'BusyTest.exe','cpu_percent_of_machine':27.4}], 'changes_made':False,'limitations':'Short CPU-time sample normalized across all logical processors; not a diagnosis or Task Manager CPU Utility.'}
            if name=='desktop_observe' and active and active[-1]=='task_manager':return {'simulation':True,'snapshot':'fixture','observations':'Task Manager foreground. Processes tab visible. CPU column visible.'}
            if name=='desktop_observe':return {'simulation':True,'snapshot':'fixture','observations':
                'Microsoft Edge foreground. Address: https://www.google.com/search?q=computer+speed+test . Page heading: computer speed test - Google Search. Search results visible.' if submitted else
                'Microsoft Edge foreground. Address: https://www.google.com/ . Page heading: Google. [control 11] (100,100) edit "Search" [action: fill] [value: "'+(typed[-1] if typed else '')+'"]. [control 12] (150,150) button "Google Search" [action: click].'}
            if name=='desktop_interact':
                args=call['function']['arguments']
                arguments.append(args)
                if args.get('action')=='type':typed.append(args.get('text',''))
                if args.get('enter') or (args.get('action')=='click' and args.get('element')==12):submitted.append(typed[-1] if typed else args.get('text',''))
                return {'simulation':True,'completion_verified':False,'result':'Typed into observed control; inspect result'}
            if name=='create_desktop_text':return {'simulation':True,'created':True,'content_verified':True,'path':'SIMULATED Desktop/Simplicity Test.txt'}
            if name=='get_recovery_tool_catalog':return original(call)
            raise ValueError('Unexpected tool blocked in synthetic test: '+name)
        agent.state.execute=simulated
        try:
            agent.run(prompt,chunks.append)
            reply=''.join(chunks)
            labelled=not (expected & {'open_desktop_app','create_desktop_text'}) or 'simulat' in reply.lower()
            complete='desktop_interact' not in expected or bool(submitted)
            if 'get_cpu_process_snapshot' in expected:complete=complete and 'BusyTest.exe' in reply
            reports.append({'expected':sorted(expected),'called':calls,'passed':expected<=set(calls) and labelled and complete,'reply':reply})
        except Exception as error:
            reports.append({'expected':sorted(expected),'called':calls,'passed':False,'error':str(error),
                            'arguments':arguments,'drafts':[message.get('content') for message in agent.state.messages if message.get('role')=='assistant' and message.get('content')]})
        finally:agent.state.close()
    print(json.dumps({'simulation_only':True,'cases':reports},ensure_ascii=True))
    if not all(report['passed'] for report in reports):raise SystemExit(1)


if __name__=='__main__':run()
