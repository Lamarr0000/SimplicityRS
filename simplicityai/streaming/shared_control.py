"""Lazy connection to the shared controller; does not import the visual UI/model."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent.parent/'visual-agent'
if str(SOURCE) not in sys.path:sys.path.append(str(SOURCE))
from control_session import ControlSession, Locator, Condition
from windows_adapter import WindowsAdapter, available_controls
from outcome_verifier import collect
from desktop_identity import window_identity
from windows_integrity import require_input_rights

DENIED={'regedit.exe','mmc.exe','diskpart.exe','datarecoveryapp.exe','windowsrecoveryapp.exe',
        'diskimagecloneapp.exe','passwordrecoveryapp.exe'}


def observe(hwnd,check):
    check()
    identity=window_identity(hwnd)
    nodes,complete=collect(hwnd,check)
    if window_identity(hwnd)!=identity:raise ValueError('Window changed during structured observation')
    return identity,available_controls(nodes) if complete else []


def click(desktop,args,check):
    if args['snapshot']!=desktop.snapshot or desktop.foreground()!=desktop.window:
        raise ValueError('Observe this desktop window before using a named control')
    import time
    if time.monotonic()-desktop.observed_at>60:raise ValueError('Desktop observation expired')
    identity=window_identity(desktop.window)
    if identity['process'] in DENIED:raise ValueError('This administration/recovery application is not enabled for desktop writes')
    locator=Locator(args.get('name',''),args.get('role',''),args.get('id',''))
    # Require the locator to describe a control that was offered in this observation.
    offered=getattr(desktop,'structured_controls',[])
    matches=[n for n in offered if (not locator.name or n['name']==locator.name)
             and (not locator.role or n['role']==locator.role)
             and (not locator.automation_id or n['id']==locator.automation_id)]
    if len(matches)!=1:raise ValueError('Control was absent or ambiguous in the latest observation')
    def guard():
        check()
        if desktop.foreground()!=identity['hwnd'] or window_identity(identity['hwnd'])!=identity:
            raise InterruptedError('Foreground window changed; no further desktop action')
        require_input_rights(identity['pid'])
    def send(point):
        guard()
        return desktop.bridge.call('Click',{'loc':point,'button':'left','clicks':1},check)
    adapter=WindowsAdapter(lambda:collect(identity['hwnd'],check),guard,send)
    desktop.snapshot=None
    result=ControlSession(adapter,check).act('click',locator)
    return {**result,'completion_verified':False,'observation_tool':'desktop_observe',
            'next':'Read the resulting window before another action or a completion report'}
