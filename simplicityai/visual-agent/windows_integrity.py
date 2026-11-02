"""Read-only Windows token checks before input injection. No token changes/elevation."""
import ctypes
from ctypes import wintypes as w
import os

kernel=ctypes.WinDLL('kernel32',use_last_error=True)
advapi=ctypes.WinDLL('advapi32',use_last_error=True)
kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]
kernel.OpenProcess.restype=w.HANDLE
kernel.CloseHandle.argtypes=[w.HANDLE]
advapi.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,ctypes.POINTER(w.HANDLE)]
advapi.GetTokenInformation.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD,ctypes.POINTER(w.DWORD)]
advapi.GetSidSubAuthorityCount.argtypes=[w.LPVOID]
advapi.GetSidSubAuthorityCount.restype=ctypes.POINTER(ctypes.c_ubyte)
advapi.GetSidSubAuthority.argtypes=[w.LPVOID,w.DWORD]
advapi.GetSidSubAuthority.restype=ctypes.POINTER(w.DWORD)


def process_security(pid):
    process=kernel.OpenProcess(0x1000,False,pid)
    if not process:raise PermissionError('Cannot query target process permissions; no input allowed')
    token=w.HANDLE()
    try:
        if not advapi.OpenProcessToken(process,8,ctypes.byref(token)):
            raise PermissionError('Cannot query target token; no input allowed')
        needed=w.DWORD()
        advapi.GetTokenInformation(token,25,None,0,ctypes.byref(needed))
        if not needed.value:raise PermissionError('Integrity information unavailable')
        buffer=ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token,25,buffer,needed,ctypes.byref(needed)):
            raise PermissionError('Integrity query failed')
        sid=ctypes.cast(buffer,ctypes.POINTER(w.LPVOID))[0]
        count=advapi.GetSidSubAuthorityCount(sid)[0]
        rid=advapi.GetSidSubAuthority(sid,count-1)[0]
        uiaccess=w.DWORD()
        if not advapi.GetTokenInformation(token,26,ctypes.byref(uiaccess),4,ctypes.byref(needed)):
            raise PermissionError('UIAccess query failed')
        return {'pid':pid,'integrity_rid':rid,'ui_access':bool(uiaccess.value)}
    finally:
        if token:kernel.CloseHandle(token)
        kernel.CloseHandle(process)


def may_inject(source,target):
    return (source['integrity_rid']>=target['integrity_rid'] or
            source['ui_access'] and target['integrity_rid']<=0x3000)


def require_input_rights(pid):
    source=process_security(os.getpid())
    target=process_security(pid)
    if not may_inject(source,target):
        raise PermissionError('Windows blocks this input: target is elevated above the preview. '
            'No input sent. Use SimplicityAI Desktop Preview (Admin) and approve Windows UAC.')
    return {'source':source,'target':target}
