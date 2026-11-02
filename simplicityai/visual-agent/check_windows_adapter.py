"""Small real Calculator adapter check. No model, microphone or user documents."""
import json
import time
from pathlib import Path
from desktop_preview import window_identity, user32, activate_requested_window
from desktop_tools import launch_app
from desktop_bridge import DesktopBridge
from windows_integrity import require_input_rights
from window_wait import wait_for_launch
from outcome_verifier import collect
from control_session import ControlSession, Locator, Condition
from windows_adapter import WindowsAdapter


def main():
    expected=('calculatorapp.exe','calculator.exe')
    before=user32.GetForegroundWindow()
    launch_app('calculator')
    identity=wait_for_launch(expected,before,user32.GetForegroundWindow,user32.IsWindow,
        window_identity,lambda:None,activate=lambda:activate_requested_window(expected))
    require_input_rights(identity['pid'])
    def guard():
        if window_identity(user32.GetForegroundWindow())!=identity:
            raise InterruptedError('Foreground changed; test stopped')
        require_input_rights(identity['pid'])
    bridge=DesktopBridge()
    results=[]
    try:
        bridge._start(guard)
        adapter=WindowsAdapter(lambda:collect(identity['hwnd'],guard),guard,
            lambda point:bridge.call('Click',{'loc':point,'button':'left','clicks':1},guard))
        session=ControlSession(adapter,guard)
        for button,result in [('clearButton','0'),('num7Button','7'),('clearButton','0')]:
            row=session.act('click',Locator(role='button',automation_id=button),
                expected=Condition(Locator(automation_id='CalculatorResults'),'name','Display is '+result))
            results.append(row)
            if not row['outcome_verified']:raise AssertionError('Actual Calculator display did not match')
    finally:
        bridge.close()
    path=Path('C:/SimplicityAI-Lab/ControlAdapter/windows-check.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'checks':len(results),'report':str(path)}))


if __name__=='__main__':main()
