"""Normal window management from fresh HWND observations; never process killing."""
import time
import os
import uuid
from pathlib import Path
import psutil
import win32gui
import win32process
import win32con


class WindowControl:
    def __init__(self):self.observed={};self.when=0

    def observe(self):
        rows=[];self.observed={}
        def visit(handle,_):
            if not win32gui.IsWindowVisible(handle):return
            title=win32gui.GetWindowText(handle)
            if not title or win32gui.GetClassName(handle) in {'Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'}:return
            try:
                pid=win32process.GetWindowThreadProcessId(handle)[1];process=psutil.Process(pid)
                path=process.exe();created=process.create_time()
            except psutil.Error:return
            expected=(Path(os.environ.get('SIMPLICITY_STREAM_ASSETS','C:/SimplicityAI-Lab/StreamingPrototype'))/'window-runtime/SimplicityAI.exe').resolve()
            own=os.path.normcase(str(Path(path).resolve()))==os.path.normcase(str(expected))
            key=uuid.uuid4().hex[:8]
            row={'id':key,'title':title,'process':Path(path).name,'minimized':bool(win32gui.IsIconic(handle)),'assistant_window':own}
            self.observed[key]={'handle':handle,'pid':pid,'created':created,'title':title,'own':own};rows.append(row)
        win32gui.EnumWindows(visit,None);self.when=time.monotonic()
        return {'windows':rows,'scope':'current desktop only','changes_made':False}

    def manage(self,action,key,check_stop):
        if time.monotonic()-self.when>60:raise ValueError('Window list expired; observe windows again')
        if action=='minimize_others':
            if not any(row['own'] for row in self.observed.values()):raise ValueError('SimplicityAI window could not be identified; no windows minimized')
            selected=[row for row in self.observed.values() if not row['own']]
        else:
            if key not in self.observed:raise ValueError('Window was not observed')
            selected=[self.observed[key]]
        results=[]
        for row in selected:
            check_stop();handle=row['handle']
            if row['own']:raise ValueError('Use SimplicityAI Exit to close its service and window')
            if not win32gui.IsWindow(handle) or win32gui.GetWindowText(handle)!=row['title']:raise ValueError('Window changed; observe it again')
            if psutil.Process(row['pid']).create_time()!=row['created']:raise ValueError('Window process changed')
            if action=='close':win32gui.PostMessage(handle,win32con.WM_CLOSE,0,0)
            else:win32gui.ShowWindow(handle,win32con.SW_MINIMIZE)
            deadline=time.monotonic()+1.5
            while time.monotonic()<deadline:
                check_stop()
                if not win32gui.IsWindow(handle) or (action!='close' and win32gui.IsIconic(handle)):break
                time.sleep(.05)
            verified=not win32gui.IsWindow(handle) if action=='close' else bool(win32gui.IsIconic(handle))
            results.append({'title':row['title'],'verified':verified})
        return {'action':action,'results':results,'all_verified':all(row['verified'] for row in results),
                'method':'Normal WM_CLOSE or minimize; no process termination, unsaved prompt dismissal or permission bypass'}
