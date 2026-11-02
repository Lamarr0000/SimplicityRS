"""Native, bounded Windows screenshot-agent lab. No general desktop access."""
import base64
import concurrent.futures
import ctypes
from ctypes import wintypes
import io
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
import urllib.request

from PIL import ImageGrab
from probe import ROOT, parse_click

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parent/'streaming'))
from desktop_bridge import DesktopBridge
from server_job import guard_server

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.WindowFromPoint.argtypes = [wintypes.POINT]
user32.WindowFromPoint.restype = wintypes.HWND
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except (AttributeError, OSError):
    pass

TASKS = {
    'Drive report': ('Open Storage, then Drive space report. Finish when the drive report is visible.', 'drive-report'),
    'Device details': ('Open Devices, then inspect the missing-driver device. Finish when its details are visible.', 'device-detail'),
    'Network report': ('Open Network, then Connection report. Finish when the connection report is visible.', 'network-report'),
}


class Lab:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('SimplicityAI Visual Agent Lab - offline test')
        self.window.configure(bg='#101722')
        self.window.resizable(False, False)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.window.bind('<Escape>', lambda _: self.stop())
        self.pending = queue.Queue()
        self.cancel = threading.Event()
        self.closed = threading.Event()
        self.worker = None
        self.server = None
        self.guard = None
        self.bridge = DesktopBridge()
        self.key = secrets.token_urlsafe(32)
        self.run_id = 0
        self.page = 'home'
        self.revision = 0
        self.moves = 0
        self.ready = False
        self.records = []
        self.log_path = None
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        header = tk.Frame(self.window, bg='#101722')
        header.pack(fill='x', padx=18, pady=12)
        tk.Label(header, text='SimplicityAI | Offline Visual Agent Lab', fg='white', bg='#101722',
                 font=('Segoe UI', -23, 'bold')).pack(side='left')
        tk.Button(header, text='Exit', command=self.close).pack(side='right')
        tk.Label(self.window, text='Test area only. Sample data, not a diagnosis of this PC. Esc or Stop ends input.',
                 fg='#c0cde3', bg='#101722', font=('Segoe UI', -16)).pack(anchor='w', padx=18)
        bar = tk.Frame(self.window, bg='#101722')
        bar.pack(fill='x', padx=18, pady=10)
        self.choice = ttk.Combobox(bar, values=list(TASKS), state='readonly', width=22)
        self.choice.set('Drive report')
        self.choice.pack(side='left', padx=(0,10))
        self.start_button = tk.Button(bar, text='Start visual test', command=self.start, state='disabled')
        self.start_button.pack(side='left', padx=5)
        tk.Button(bar, text='Stop', command=self.stop).pack(side='left', padx=5)
        tk.Button(bar, text='Copy evidence', command=self.copy).pack(side='right')
        self.status = tk.StringVar(value='Loading local vision model; first startup can take a minute...')
        tk.Label(self.window, textvariable=self.status, fg='#a8c9ff', bg='#101722',
                 font=('Segoe UI', -16), wraplength=1080, anchor='w').pack(fill='x', padx=18, pady=(0,10))
        self.canvas = tk.Canvas(self.window, width=1120, height=784, bg='#edf1f7',
                                highlightthickness=0, borderwidth=0)
        self.canvas.pack(padx=18, pady=(0,14))
        self.canvas.bind('<Button-1>', self.clicked)
        self.draw()
        self.window.update_idletasks()
        self.hwnd = user32.GetAncestor(self.window.winfo_id(), 2)
        self.window.after(30, self.pump)
        threading.Thread(target=self.load_model, daemon=True).start()

    def ui(self, function):
        future = concurrent.futures.Future()
        self.pending.put((function,future))
        return future.result(timeout=8)

    def pump(self):
        try:
            while True:
                function, future = self.pending.get_nowait()
                if future.set_running_or_notify_cancel():
                    try: future.set_result(function())
                    except BaseException as error: future.set_exception(error)
        except queue.Empty:
            pass
        self.window.after(30, self.pump)

    def request(self, path, payload=None, timeout=90):
        headers = {'Authorization':'Bearer '+self.key}
        data = None
        if payload is not None:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(payload).encode()
        req = urllib.request.Request('http://127.0.0.1:8772'+path, data, headers)
        with self.opener.open(req, timeout=timeout) as response:
            return json.load(response)

    def load_model(self):
        try:
            if self.closed.is_set(): return
            # Refuse an already competing GPU model instead of silently paging two
            # multi-GB agents through this host's 8 GB GPU. Read-only preflight.
            try:
                with self.opener.open('http://127.0.0.1:11434/api/ps',timeout=2) as response:
                    residents = json.load(response).get('models',[])
                competing = [model.get('name','unknown') for model in residents
                             if model.get('size_vram',0)>1024**3]
            except (OSError,ValueError):
                competing = []
            if competing:
                raise RuntimeError('Another GPU model is loaded ('+', '.join(competing)+
                    '). Close regular SimplicityAI and unload that Ollama model before opening this lab.')
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',8772))
            env = dict(os.environ, LLAMA_API_KEY=self.key)
            args = [str(ROOT/'runtime/llama-server.exe'), '-m', str(ROOT/'UI-TARS-1.5-7B.Q4_K_M.gguf'),
                    '--mmproj', str(ROOT/'UI-TARS-1.5-7B.mmproj-f16.gguf'), '--host','127.0.0.1',
                    '--port','8772','--alias','ui-tars','-c','4096','-ngl','99','-t','6',
                    '--parallel','1','--image-min-tokens','1024','--cors-origins','http://127.0.0.1:8772']
            with (ROOT/'lab-server.log').open('ab') as output:
                if self.closed.is_set(): return
                self.server = subprocess.Popen(args, env=env, stdout=output, stderr=output,
                    stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self.guard = guard_server(self.server)
            if self.closed.is_set():
                self.server.terminate()
                self.guard()
                return
            deadline = time.monotonic()+150
            while time.monotonic()<deadline:
                if self.closed.is_set(): return
                if self.server.poll() is not None: raise RuntimeError('Model server exited; see lab-server.log')
                try:
                    if self.request('/health',timeout=2).get('status') == 'ok': break
                except (OSError,ValueError): pass
                time.sleep(.5)
            else: raise TimeoutError('Model startup exceeded 150 seconds')
            self.ui(lambda:self.set_ready())
        except BaseException as error:
            if not self.closed.is_set():
                self.ui(lambda error=error:self.status.set('Startup failed: '+str(error)))

    def set_ready(self):
        self.ready = True
        self.start_button.configure(state='normal')
        self.status.set('Ready. Choose a test and click Start visual test. Keep this window visible.')

    def draw(self):
        c = self.canvas
        c.delete('all')
        c.create_text(36,38,text='Recovery diagnostics - SAMPLE TEST DATA',anchor='w',
                      font=('Segoe UI',-24,'bold'),fill='#152138')
        menus = {
            'home':('Choose a diagnostic area',[('Storage','storage'),('Devices','devices'),('Network','network')]),
            'storage':('Storage checks',[('Drive space report','drive-report'),('Back','home')]),
            'devices':('Devices',[('Audio: missing driver','device-detail'),('Back','home')]),
            'network':('Network checks',[('Connection report','network-report'),('Back','home')]),
            'drive-report':('Drive report - SAMPLE: C: 80 GB free of 128 GB',[('Back','home')]),
            'device-detail':('Device details - SAMPLE: Audio, driver not installed (Code 28)',[('Back','home')]),
            'network-report':('Connection report - SAMPLE: DNS resolved example.test',[('Back','home')]),
        }
        title, buttons = menus[self.page]
        c.create_text(36,140,text=title,anchor='w',font=('Segoe UI',-23),fill='#152138')
        self.boxes = []
        # Rearrange on navigation, so a repeated center click cannot complete a task.
        positions = [760,50,405] if self.moves % 2 else [50,760,405]
        for index,(label,target) in enumerate(buttons):
            left = positions[index]
            box = (left,260,left+310,350)
            self.boxes.append((box,target))
            c.create_rectangle(*box,fill='#244c85',outline='#244c85')
            c.create_text(left+155,305,text=label,fill='white',font=('Segoe UI',-22))
        c.create_text(36,650,text='This agent can click only inside this test area. It cannot operate other apps.',
                      anchor='w',font=('Segoe UI',-19),fill='#35465f')
        self.revision += 1

    def clicked(self,event):
        for (left,top,right,bottom),target in self.boxes:
            if left<=event.x<=right and top<=event.y<=bottom:
                self.page = target
                self.moves += 1
                self.draw()
                return

    def check(self):
        if self.cancel.is_set(): raise InterruptedError('Stopped; no further input will be sent')

    def capture(self):
        self.check()
        self.window.update_idletasks()
        if user32.GetForegroundWindow() != self.hwnd:
            raise InterruptedError('Test window lost foreground; stopped without clicking')
        left,top = self.canvas.winfo_rootx(),self.canvas.winfo_rooty()
        width,height = self.canvas.winfo_width(),self.canvas.winfo_height()
        if (width,height)!=(1120,784): raise RuntimeError('Unexpected canvas dimensions')
        if left<0 or top<0 or left+width>self.window.winfo_screenwidth() or top+height>self.window.winfo_screenheight():
            raise RuntimeError('Test area must be entirely on the primary screen')
        for x,y in [(left+3,top+3),(left+width-3,top+height-3),(left+width//2,top+height//2)]:
            owner = user32.GetAncestor(user32.WindowFromPoint(wintypes.POINT(x,y)),2)
            if owner != self.hwnd: raise InterruptedError('Test area is covered; stopped')
        image = ImageGrab.grab(bbox=(left,top,left+width,top+height),all_screens=True)
        return image,(left,top,width,height),self.revision

    def validate_click(self, point, rectangle, revision):
        self.check()
        left,top,width,height = rectangle
        current = (self.canvas.winfo_rootx(),self.canvas.winfo_rooty(),self.canvas.winfo_width(),self.canvas.winfo_height())
        if current!=rectangle or self.revision!=revision: raise InterruptedError('Window or content changed during inference')
        if user32.GetForegroundWindow()!=self.hwnd: raise InterruptedError('Foreground changed; stopped')
        x,y = point
        if not (0<=x<width and 0<=y<height): raise ValueError('Point outside test area')
        screen = [left+round(x),top+round(y)]
        if user32.GetAncestor(user32.WindowFromPoint(wintypes.POINT(*screen)),2)!=self.hwnd:
            raise InterruptedError('Another window covers the click point')
        return screen

    def start(self):
        if not self.ready or (self.worker and self.worker.is_alive()): return
        self.cancel.clear()
        self.page = 'home'
        self.moves = 0
        self.draw()
        self.start_button.configure(state='disabled')
        self.run_id += 1
        self.records = []
        self.log_path = ROOT/f'windows-lab-{time.strftime("%Y%m%d-%H%M%S")}-{self.run_id}.json'
        task,target = TASKS[self.choice.get()]
        self.status.set('Running visual task. Keep the test window visible; Esc or Stop cancels.')
        self.worker = threading.Thread(target=self.run,args=(task,target),daemon=True)
        self.worker.start()

    def save(self, row):
        self.records.append(row)
        self.flush()

    def flush(self):
        self.log_path.write_text(json.dumps({'real_windows_input':True,'scope':'owned lab canvas only',
            'records':self.records},indent=2),encoding='utf-8')

    def run(self,task,target):
        run_started = time.perf_counter()
        try:
            # Initialize the existing local Windows-MCP driver before the first observation.
            phase = time.perf_counter()
            self.bridge._start(self.check)
            self.save({'phase':'driver_startup','seconds':round(time.perf_counter()-phase,3)})
            history = []
            deadline = time.monotonic()+180
            for step in range(12):
                self.check()
                if time.monotonic()>deadline: raise TimeoutError('Task time limit reached')
                phase = time.perf_counter()
                image,rectangle,revision = self.ui(self.capture)
                capture_seconds = round(time.perf_counter()-phase,3)
                page_before = self.ui(lambda:self.page)
                image.save(ROOT/f'windows-lab-latest.png')
                stream = io.BytesIO();image.save(stream,'PNG')
                prompt = ("You are a GUI agent. Use the screenshot to choose the next action. "
                    "Output exactly one line: Action: click(start_box='(x,y)') or Action: finished(). "
                    "Coordinates use screenshot pixels. Click one control at a time. "
                    "Finish only when the requested details/report are visible.\n"
                    f"Task: {task}\nPrevious actions: {history}")
                payload = {'model':'ui-tars','temperature':0,'max_tokens':128,'messages':[
                    {'role':'user','content':[{'type':'text','text':prompt},
                     {'type':'image_url','image_url':{'url':'data:image/png;base64,'+
                        base64.b64encode(stream.getvalue()).decode()}}]}]}
                self.ui(lambda step=step:self.status.set(f'Looking at the test window - decision {step+1}...'))
                started = time.perf_counter()
                data = self.request('/v1/chat/completions',payload)
                elapsed = round(time.perf_counter()-started,3)
                self.check()
                output = data['choices'][0]['message']['content'].strip()
                row = {'step':step,'seconds':elapsed,'model_seconds':elapsed,
                       'capture_seconds':capture_seconds,'output':output,'page_before':page_before,
                       'model_timings':data.get('timings',{}),
                       'elapsed_seconds':round(time.perf_counter()-run_started,3)}
                if output in ('Action: finished()', 'finished()'):
                    verified = self.ui(lambda:self.page==target)
                    row['verified_complete'] = verified
                    self.save(row)
                    if not verified: raise RuntimeError('Model claimed completion before the requested screen appeared')
                    self.ui(lambda:self.status.set(f'Passed: actual Windows clicks, report verified. Evidence: {self.log_path.name}'))
                    return
                self.save(row)
                point = parse_click(output,*image.size)
                screen = self.ui(lambda:self.validate_click(point,rectangle,revision))
                self.check()
                phase = time.perf_counter()
                observation = self.bridge.call('Click',{'loc':screen,'button':'left','clicks':1},self.check)
                row.update(point=point,driver=observation,driver_seconds=round(time.perf_counter()-phase,3),
                           page_after=self.ui(lambda:self.page))
                self.flush()
                history.append(output)
                time.sleep(.35)
            raise RuntimeError('Step limit reached; completion unverified')
        except BaseException as error:
            self.save({'stopped':True,'reason':str(error)})
            self.ui(lambda error=error:self.status.set(str(error)))
        finally:
            self.ui(lambda:self.start_button.configure(state='normal'))

    def stop(self):
        self.cancel.set()
        self.status.set('Stopped. A pending model request may finish, but its action will not run.')

    def copy(self):
        self.window.clipboard_clear()
        self.window.clipboard_append(json.dumps(self.records,indent=2))

    def close(self):
        self.closed.set()
        self.cancel.set()
        self.bridge.close()
        if self.server is not None and self.server.poll() is None:
            self.server.terminate()
        if self.guard: self.guard()
        self.window.destroy()


if __name__ == '__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    Lab().window.mainloop()
