"""Shared read-only Windows target identity; no UI launch or input at import."""
import ctypes
from ctypes import wintypes
import psutil
user32=ctypes.WinDLL('user32',use_last_error=True)
user32.IsWindow.argtypes=[wintypes.HWND]
user32.IsWindow.restype=wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
user32.GetForegroundWindow.restype=wintypes.HWND
BLOCKED={'cmd.exe','powershell.exe','pwsh.exe','windowsterminal.exe','consent.exe',
         'credentialuibroker.exe','lockapp.exe','securityhealthsystray.exe','sechealthui.exe',
         'codex.exe','chatgpt.exe','vmware.exe','vmplayer.exe','virtualboxvm.exe','mstsc.exe'}


def window_identity(hwnd):
    if not hwnd or not user32.IsWindow(hwnd):raise InterruptedError('No interactive window')
    pid=wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    process=psutil.Process(pid.value)
    title=ctypes.create_unicode_buffer(1024)
    user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user32.GetWindowTextW(hwnd,title,len(title))
    name=process.name().lower()
    host_pid=None
    if name=='applicationframehost.exe':
        import win32gui
        hosted={}
        def child_process(child,_):
            child_pid=wintypes.DWORD()
            user32.GetWindowThreadProcessId(child,ctypes.byref(child_pid))
            try:
                item=psutil.Process(child_pid.value)
                if item.name().lower() in {'calculatorapp.exe','calculator.exe'}:
                    hosted[item.pid]=item
            except psutil.Error:pass
        win32gui.EnumChildWindows(hwnd,child_process,None)
        if len(hosted)==1:
            host_pid=pid.value
            process=next(iter(hosted.values()))
            pid.value=process.pid
            name=process.name().lower()
    if name in BLOCKED or any(label in title.value.lower() for label in
            ('user account control','windows security','choose a passkey','password manager')):
        raise InterruptedError('Protected application/dialog: return control to the user')
    rect=wintypes.RECT()
    user32.GetWindowRect(hwnd,ctypes.byref(rect))
    return {'hwnd':int(hwnd),'pid':pid.value,'created':process.create_time(),'process':name,
            'title':title.value,'rect':(rect.left,rect.top,rect.right,rect.bottom),'host_pid':host_pid}
