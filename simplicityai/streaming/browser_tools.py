"""One bounded ThemHands action: open Edge's blank window and observe it.

No arbitrary path/URL, keys, clicks, history, downloads, profile or settings access.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import time

import psutil


def edge_path():
    for variable in ('ProgramFiles(x86)','ProgramFiles'):
        base=os.environ.get(variable)
        if base:
            path=Path(base)/'Microsoft/Edge/Application/msedge.exe'
            if path.is_file():return path.resolve()
    return None


class Windows:
    def __init__(self):
        self.api=ctypes.WinDLL('user32',use_last_error=True)
        self.callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        self.api.EnumWindows.argtypes=[self.callback,wintypes.LPARAM]
        self.api.IsWindowVisible.argtypes=[wintypes.HWND]
        self.api.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        self.api.GetForegroundWindow.restype=wintypes.HWND
        self.api.SetForegroundWindow.argtypes=[wintypes.HWND]
        self.api.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int]

    def matching(self,path):
        handles=[];expected=os.path.normcase(str(path))
        @self.callback
        def visit(handle,_):
            try:
                pid=wintypes.DWORD()
                self.api.GetWindowThreadProcessId(handle,ctypes.byref(pid))
                if self.api.IsWindowVisible(handle) and os.path.normcase(psutil.Process(pid.value).exe())==expected:
                    handles.append(int(handle))
            except (psutil.Error,OSError):pass
            return True
        self.api.EnumWindows(visit,0)
        return handles

    def foreground(self,handle):
        self.api.ShowWindow(handle,9)  # SW_RESTORE; no synthetic input/focus bypass.
        self.api.SetForegroundWindow(handle)
        return self.api.GetForegroundWindow()==handle


def launch(path):
    # User apps must survive assistant Exit. The launcher permits this explicit
    # breakaway; speech/collector workers keep their existing kill-on-close jobs.
    return subprocess.Popen([str(path),'--new-window','about:blank'],shell=False,
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_BREAKAWAY_FROM_JOB)


def open_browser(check_stop,emit,timeout=15):
    path=edge_path()
    if path is None:
        return {'ok':False,'browser':'Microsoft Edge','new_window_observed':False,
                'error':'Edge was not found in its standard installation locations. Other browsers were not inspected.'}
    check_stop();windows=Windows();before=set(windows.matching(path))
    emit('action','ThemHands is opening a blank Microsoft Edge window and checking whether it appears. This does not test the internet.')
    try:process=launch(path)
    except OSError as error:
        return {'ok':False,'browser':'Microsoft Edge','new_window_observed':False,'error':str(error),
                'internet_tested':False}
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        check_stop();created=[h for h in windows.matching(path) if h not in before]
        if created:
            handle=created[0];front=windows.foreground(handle)
            return {'ok':True,'tool_layer':'ThemHands','scope':'Windows running SimplicityAI only',
                    'browser':'Microsoft Edge','test_page':'about:blank','new_window_observed':True,
                    'window_handle':handle,'foreground_verified':front,'internet_tested':False,
                    'limitations':['A browser window appeared; page rendering, responsiveness and web access were not tested.',
                                   'This does not establish whether a different/default browser is working.'],
                    'settings_changed':False}
        time.sleep(.1)
    return {'ok':False,'browser':'Microsoft Edge','launch_requested':True,'new_window_observed':False,
            'launcher_exit_code':process.poll(),'internet_tested':False,
            'error':'No new visible Edge window was verified within the time limit. The cause is unknown.'}


def browser_report(result):
    """A window-only observation must never turn into an invented network fault."""
    prefix='SIMULATION ONLY; no browser was opened. ' if result.get('simulation') else ''
    if result.get('ok') and result.get('new_window_observed'):
        focus=('It is in the foreground.' if result.get('foreground_verified') else
               'It may be behind this window; check its taskbar button.')
        opening='The synthetic fixture reports a new Microsoft Edge window.' if result.get('simulation') else 'Microsoft Edge opened a new window.'
        return prefix+(opening+' '+focus+
                ' This was a blank-window launch test; website loading has not been tested. '
                'Was Edge the browser that would not open, or was it a different browser?')
    return prefix+('I could not verify a new Microsoft Edge window. '+result.get('error','The cause is unknown.')+
            ' This does not establish an internet problem. Which browser were you trying to open?')
