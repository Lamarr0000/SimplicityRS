"""Opt-in real Voice Pilot named-control path, without model or microphone."""
import json
from pathlib import Path
from desktop_tools import DesktopTools, launch_app
from shared_control import collect, window_identity
from desktop_preview import activate_requested_window, user32
from window_wait import wait_for_launch


def main():
    check=lambda:None
    expected=('calculatorapp.exe','calculator.exe')
    before=user32.GetForegroundWindow()
    launch_app('calculator')
    identity=wait_for_launch(expected,before,user32.GetForegroundWindow,user32.IsWindow,
        window_identity,check,activate=lambda:activate_requested_window(expected))
    desktop=DesktopTools()
    results=[]
    try:
        for button,display in [('clearButton','0'),('num7Button','7'),('clearButton','0')]:
            observation=desktop.observe(check)
            assert any(n['id']==button for n in observation['structured_controls'])
            args={'snapshot':observation['snapshot'],'role':'button','id':button}
            results.append(desktop.execute('desktop_click_control',args,check))
            nodes,complete=collect(identity['hwnd'],check)
            assert complete and any(n.get('automation_id')=='CalculatorResults' and n['name']=='Display is '+display for n in nodes)
            try:desktop.execute('desktop_click_control',args,check)
            except ValueError:pass
            else:raise AssertionError('Consumed desktop snapshot was replayed')
    finally:desktop.close()
    path=Path('C:/SimplicityAI-Lab/ControlAdapter/voice-desktop-check.json')
    path.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'checks':len(results),'report':str(path)}))


if __name__=='__main__':main()
