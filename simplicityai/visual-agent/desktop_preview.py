"""Offline screenshot agent for ordinary applications on the primary Windows desktop."""
import base64
import ctypes
from ctypes import wintypes
import io
import json
import os
import threading
import time
import tkinter as tk
from tkinter import ttk

import psutil
from PIL import ImageGrab
from desktop_lab import Lab, ROOT, user32
from desktop_bridge import DesktopBridge, ALLOWED
from desktop_actions import decode, to_screen, requested_app, action_context_error
from agent_context import AgentContext
from windows_integrity import require_input_rights
from window_wait import wait_for_launch
from outcome_verifier import CASES, TEST_TEXT, collect, verify
from suite_report import summarize
from acceptance_guard import bind_document, check_document, require_document_action, require_calculator_action
from desktop_tools import DESKTOP_TOOLS,launch_app

LAUNCH_APPS=next(tool['function']['parameters']['properties']['app']['enum']
                for tool in DESKTOP_TOOLS if tool['function']['name']=='open_desktop_app')

user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
user32.GetWindow.argtypes=[wintypes.HWND,wintypes.UINT]
user32.GetWindow.restype=wintypes.HWND
user32.IsWindowVisible.argtypes=[wintypes.HWND]
user32.IsIconic.argtypes=[wintypes.HWND]
user32.SetForegroundWindow.argtypes=[wintypes.HWND]
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


def activate_requested_window(expected):
    """Normal foreground request for the newest observed matching app; no focus bypass."""
    import win32gui
    expected={expected} if isinstance(expected,str) else set(expected)
    candidates=[]
    def visit(hwnd,_):
        if not user32.IsWindowVisible(hwnd):return
        try:
            identity=window_identity(hwnd)
            if identity['process'] in expected and identity['title']:
                candidates.append((identity['created'],hwnd))
        except (InterruptedError,psutil.Error,OSError):pass
    win32gui.EnumWindows(visit,None)
    if candidates:
        newest=max(created for created,hwnd in candidates)
        matches=[hwnd for created,hwnd in candidates if created==newest]
        if len(matches)==1:user32.SetForegroundWindow(matches[0])


class Preview(Lab):
    def __init__(self, task=None, acceptance_case=None, batch=False, suite_cases=None):
        self.batch_active=False
        self.batch_pending=[]
        self.batch_results=[]
        self.batch_report=None
        self.auto_batch=batch
        self.suite_cases=suite_cases or ['task-manager-performance','task-manager-cpu','calculator-addition']
        self.acceptance_case=acceptance_case
        super().__init__()
        self.window.title('SimplicityAI Desktop Preview - offline')
        self.canvas.pack_forget()
        self.choice.pack_forget()
        # Replace test-area copy with accurate desktop scope.
        for child in self.window.winfo_children():
            if isinstance(child,tk.Label) and 'Test area only' in str(child.cget('text')):
                child.configure(text='Offline primary-desktop control. Stop or move the mouse to take over. UAC remains yours.')
        self.case_choice=ttk.Combobox(self.window,state='readonly',width=35,
            values=['Custom task',*CASES])
        self.case_choice.pack(before=self.start_button.master,padx=18,pady=4)
        self.case_choice.set(acceptance_case or 'Custom task')
        self.case_choice.bind('<<ComboboxSelected>>',self.choose_case)
        self.taskbox=tk.Text(self.window,height=3,width=90,font=('Segoe UI',-18),wrap='word')
        self.taskbox.pack(before=self.start_button.master,fill='x',padx=18,pady=10)
        if task:
            self.taskbox.delete('1.0','end')
            self.taskbox.insert('1.0',task)
        self.start_button.configure(text='Start task')
        self.suite_button=tk.Button(self.start_button.master,text='Run acceptance suite',command=self.start_suite,state='disabled')
        self.suite_button.pack(side='left',padx=5)
        self.window.resizable(True,False)
        self.window.geometry('1100x500')
        for child in self.window.winfo_children()[0].winfo_children():
            if isinstance(child,tk.Label):child.configure(text='SimplicityAI | Offline Desktop Preview')
        self.bridge=DesktopBridge(allowed=ALLOWED|{'Move'})

    def choose_case(self,event=None):
        case=self.case_choice.get()
        self.acceptance_case=case if case in CASES else None
        if self.acceptance_case:
            self.taskbox.delete('1.0','end')
            self.taskbox.insert('1.0',CASES[case][1])

    def set_ready(self):
        self.ready=True
        self.suite_button.configure(state='normal')
        if self.auto_batch:
            self.auto_batch=False
            self.window.after(1500,self.start_suite)
        self.start_button.configure(state='normal')
        self.status.set('Ready. Describe a desktop task. Start minimizes this controller while the agent works.')

    def start(self):
        if not self.ready or (self.worker and self.worker.is_alive()):return
        task=self.taskbox.get('1.0','end').strip()
        if not task:return
        self.cancel.clear()
        self.records=[]
        self.run_id+=1
        self.log_path=ROOT/f'desktop-preview-{time.strftime("%Y%m%d-%H%M%S")}-{self.run_id}.json'
        self.start_button.configure(state='disabled')
        self.suite_button.configure(state='disabled')
        self.status.set('Working on the requested desktop task. Restore this controller or move the mouse to take over.')
        self.window.update_idletasks()
        self.hwnd=user32.GetAncestor(self.window.winfo_id(),2)
        target=user32.GetWindow(self.hwnd,2)
        for _ in range(40):
            if not target:break
            try:
                item=window_identity(target)
                if (item['pid']!=os.getpid() and user32.IsWindowVisible(target)
                        and not user32.IsIconic(target) and item['title']
                        and item['rect'][2]-item['rect'][0]>200):break
            except (InterruptedError,psutil.Error,OSError):pass
            target=user32.GetWindow(target,2)
        else:target=None
        explicit_launch=bool(requested_app(task,LAUNCH_APPS))
        if not target and not explicit_launch:
            self.start_button.configure(state='normal')
            self.status.set('Open the application you want to use before starting this preview.')
            return
        self.window.iconify()
        self.worker=threading.Thread(target=self.run_desktop,args=(task,),daemon=True)
        def begin():
            if self.closed.is_set():return
            if not explicit_launch and not user32.SetForegroundWindow(target):
                self.status.set('Windows did not activate the target application. No actions started.')
                self.show_controller()
                return
            self.worker.start()
        self.window.after(400,begin)

    def observe_desktop(self):
        self.check()
        hwnd=user32.GetForegroundWindow()
        if hwnd==self.hwnd:raise InterruptedError('Controller is foreground; stopped')
        identity=window_identity(hwnd)
        if identity['pid']==os.getpid():raise InterruptedError('Controller has not minimized yet; stopped')
        primary=ImageGrab.grab(all_screens=False)
        sw,sh=primary.size
        l,t,r,b=identity['rect']
        l,t,r,b=max(0,l),max(0,t),min(sw,r),min(sh,b)
        if r-l<200 or b-t<120:
            l,t,r,b=0,0,sw,sh
        image=primary.crop((l,t,r,b))
        physical={'size':image.size,'origin':(l,t)}
        # Multiples of 28 and >=1024 image tokens avoid hidden projector resizing.
        import math
        aspect=image.width/image.height
        width=max(28,math.ceil(math.sqrt(1296*784*aspect)/28)*28)
        height=max(28,math.ceil((1296*784/width)/28)*28)
        image=image.resize((width,height))
        return image,physical,identity,time.monotonic()

    def validate_desktop(self,identity,stamp,points=()):
        self.check()
        if time.monotonic()-stamp>30:raise InterruptedError('Screenshot expired; stopped')
        current=window_identity(user32.GetForegroundWindow())
        if current!=identity:raise InterruptedError('Foreground window changed during inference; stopped')
        require_input_rights(current['pid'])
        for point in points:
            hwnd=user32.GetAncestor(user32.WindowFromPoint(wintypes.POINT(*point)),2)
            if hwnd==self.hwnd:raise InterruptedError('Agent cannot operate its own controller')
            target=window_identity(hwnd)
            require_input_rights(target['pid'])

    def focused_point(self,physical):
        # Only type into an observed focused editable control; never a terminal or password field.
        from windows_mcp import uia
        with uia.UIAutomationInitializerInThread():
            focused=uia.GetFocusedControl()
            if focused.IsPassword:raise InterruptedError('Password input requires the user')
            if focused.ControlTypeName not in {'EditControl','DocumentControl','ComboBoxControl'}:
                raise ValueError('No text was entered. Focus is '+focused.ControlTypeName+
                    ', not an editable field. Click inside the document/text field, then type.')
            box=focused.BoundingRectangle
            point=[round((box.left+box.right)/2),round((box.top+box.bottom)/2)]
            left,top=physical['origin'];width,height=physical['size']
            if not (left<=point[0]<left+width and top<=point[1]<top+height):
                raise InterruptedError('Focused text field is outside the primary screen')
            return point

    def run_desktop(self,task):
        started=time.perf_counter()
        try:
            phase=time.perf_counter();self.bridge._start(self.check)
            self.save({'phase':'driver_startup','seconds':round(time.perf_counter()-phase,3),'task':task})
            history=[]
            context=AgentContext(task,LAUNCH_APPS)
            feedback=''
            parse_failures=0
            app=requested_app(task,LAUNCH_APPS)
            expected_executable=None
            case=self.acceptance_case if self.acceptance_case and task==CASES[self.acceptance_case][1] else None
            document_binding=None
            if app:
                # A directly requested utility uses the same existing catalog tool
                # as the main app; do not type a launch command into the previous app.
                before=user32.GetForegroundWindow()
                self.check();phase=time.perf_counter()
                result=launch_app(app)
                expected_executable=os.path.basename(result['executable']).lower()
                launch_expected=('calculatorapp.exe','calculator.exe') if app=='calculator' else expected_executable
                self.save({'phase':'requested_app_launch','app':app,'result':result,
                           'seconds':round(time.perf_counter()-phase,3),
                           'selection':'explicit user request + existing catalog; not model inference'})
                observed=wait_for_launch(launch_expected,before,
                    user32.GetForegroundWindow,user32.IsWindow,window_identity,self.check,
                    activate=lambda:self.ui(lambda:activate_requested_window(launch_expected)))
                self.save({'phase':'requested_app_observed','foreground':observed})
                feedback='The requested app launch tool returned: '+json.dumps(result)+'. Inspect the current window before continuing.'
            for step in range(24):
                self.check()
                if time.perf_counter()-started>240:raise TimeoutError('Four-minute task limit reached')
                image,physical,identity,stamp=self.ui(self.observe_desktop)
                if case:
                    image.save(self.log_path.with_suffix('.png'))
                    expected_processes={'calculatorapp.exe','calculator.exe'} if case=='calculator-addition' else {CASES[case][0]}
                    if identity['process'] not in expected_processes:
                        raise InterruptedError('Acceptance test requires its requested application in foreground; no input sent')
                    if case=='notepad-text':
                        nodes,complete=collect(identity['hwnd'],self.check)
                        self.ui(lambda:self.validate_desktop(identity,stamp))
                        if document_binding is None:
                            document_binding=bind_document(identity,nodes,complete)
                            self.save({'phase':'document_bound','binding':document_binding})
                        doc=check_document(document_binding,identity,nodes,complete)
                        outcome={'case':case,'verified':doc['text'].rstrip('\r\n')==TEST_TEXT,
                                 'method':'bound Notepad tab/document UI Automation',
                                 'reason':'Exact text observed in the original bound document'}
                    else:
                        outcome=verify(case,identity,window_identity,user32.GetForegroundWindow,self.check)
                    self.check()
                    if outcome['verified']:
                        self.save({'phase':'acceptance_outcome','completion_source':'application verifier',
                                   'completion_claim':False,'independent_verification':True,
                                   'outcome_verification':outcome,
                                   'elapsed_seconds':round(time.perf_counter()-started,3)})
                        self.ui(lambda:self.status.set('Acceptance outcome verified. Stopped before further model actions.'))
                        return
                # Detect UIPI before spending another model turn or reporting a click.
                input_permissions=require_input_rights(identity['pid'])
                stream=io.BytesIO();image.save(stream,'PNG')
                messages=context.observation('data:image/png;base64,'+
                    base64.b64encode(stream.getvalue()).decode(),feedback,identity['title'])
                payload={'model':'ui-tars','temperature':0,'max_tokens':256,'messages':messages}
                phase=time.perf_counter();data=self.request('/v1/chat/completions',payload)
                seconds=round(time.perf_counter()-phase,3);self.check()
                output=data['choices'][0]['message']['content'].strip()
                row={'step':step,'model_seconds':seconds,'output':output,'foreground':identity,
                     'model_timings':data.get('timings',{}),'input_permissions':input_permissions}
                self.save(row)
                context.action(output)
                try:action=decode(output,*image.size,apps=LAUNCH_APPS)
                except (ValueError, SyntaxError) as error:
                    row['parse_error']=str(error);self.flush()
                    parse_failures+=1
                    if parse_failures>=3:raise RuntimeError('Three invalid actions; stopped without executing them')
                    feedback='No action was executed: '+str(error)+'. Use one supported action from the listed tools.'
                    continue
                context_error=action_context_error(action,expected_executable,identity['process'])
                if context_error:
                    row['action_rejected']=context_error;self.flush()
                    parse_failures+=1
                    if parse_failures>=3:raise RuntimeError('Three invalid or context-inappropriate actions; stopped')
                    feedback=context_error
                    continue
                parse_failures=0
                feedback='Previous action completed; inspect the current result.'
                signature=json.dumps(action,sort_keys=True)
                if len(history)>=3 and history[-3:]==[signature]*3:
                    raise RuntimeError('Repeated action loop detected; stopped')
                if action['kind'] in {'finished','call_user'}:
                    row['completion_claim']=action['kind']=='finished'
                    outcome={'verified':False,'reason':'No independent verifier for this task'}
                    if action['kind']=='finished' and self.acceptance_case:
                        if task != CASES[self.acceptance_case][1]:
                            outcome={'verified':False,'reason':'Acceptance task was edited; verifier does not apply'}
                        elif case=='notepad-text':
                            outcome={'verified':False,'reason':'Bound document outcome was not observed'}
                        else:
                            outcome=verify(self.acceptance_case,identity,window_identity,
                                           user32.GetForegroundWindow,self.check)
                    self.check()
                    row['outcome_verification']=outcome
                    row['independent_verification']=outcome['verified']
                    row['elapsed_seconds']=round(time.perf_counter()-started,3)
                    self.flush()
                    label=('Acceptance outcome verified' if outcome['verified'] else
                           'Model reports finished; outcome unverified') if action['kind']=='finished' else 'User help needed'
                    self.ui(lambda:self.status.set(label+': '+action['content']+' — please verify the result.'))
                    return
                points=[to_screen(action[key],image.size,physical['size'],physical['origin'])
                        for key in ('point','end') if key in action]
                if action['kind']=='type':
                    try:points=[self.ui(lambda:self.focused_point(physical))]
                    except ValueError as error:
                        feedback='Tool observation: '+str(error)
                        row['tool_feedback']=feedback;self.flush()
                        continue
                if case=='notepad-text':
                    nodes,complete=collect(identity['hwnd'],self.check)
                    doc=check_document(document_binding,identity,nodes,complete)
                    require_document_action(action,doc,points)
                    if action['kind']=='type':
                        require_document_action({'kind':'click'},doc,points)
                if case=='calculator-addition':
                    nodes,complete=collect(identity['hwnd'],self.check)
                    require_calculator_action(action,nodes,complete,points)
                self.ui(lambda:self.validate_desktop(identity,stamp,points))
                self.check();phase=time.perf_counter()
                kind=action['kind']
                if kind=='open_app':
                    result=json.dumps(launch_app(action['name']))
                elif kind in {'click','left_double','right_single'}:
                    result=self.bridge.call('Click',{'loc':points[0],
                        'button':'right' if kind=='right_single' else 'left',
                        'clicks':2 if kind=='left_double' else 1},self.check)
                elif kind=='type':
                    result=self.bridge.call('Type',{'loc':points[0],'text':action['content'],
                        'clear':False,'press_enter':action['submit']},self.check)
                elif kind=='hotkey':
                    result=self.bridge.call('Shortcut',{'shortcut':action['shortcut']},self.check)
                elif kind=='scroll':
                    result=self.bridge.call('Scroll',{'loc':points[0],'direction':action['direction'],
                        'type':'horizontal' if action['direction'] in {'left','right'} else 'vertical',
                        'wheel_times':2},self.check)
                elif kind=='drag':
                    result=self.bridge.call('Move',{'from_loc':points[0],'loc':points[1],
                        'drag':True,'duration':.4},self.check)
                else:
                    if self.cancel.wait(1):self.check()
                    result='Waited for screen update'
                row.update(driver_seconds=round(time.perf_counter()-phase,3),driver=result)
                feedback='Input tool returned: '+str(result)+'. Inspect the screen to verify the outcome.'
                self.flush();history.append(signature)
                if self.cancel.wait(.3):self.check()
            raise RuntimeError('Step limit reached; completion is unverified')
        except BaseException as error:
            details={'stopped':True,'reason':str(error)}
            if error.__cause__ is not None:
                details['driver_cause']=str(error.__cause__)[:2000]
            self.save(details)
            self.ui(lambda error=error:self.status.set(str(error)))
        finally:
            self.ui(self.show_controller)

    def start_suite(self):
        if not self.ready or (self.worker and self.worker.is_alive()):return
        self.cancel.clear()
        self.batch_active=True
        self.batch_pending=list(self.suite_cases)
        self.batch_results=[]
        self.batch_report=ROOT/f'acceptance-suite-{time.strftime("%Y%m%d-%H%M%S")}.json'
        self.next_suite_case()

    def next_suite_case(self):
        if self.worker and self.worker.is_alive():
            self.window.after(100,self.next_suite_case);return
        if self.cancel.is_set() or not self.batch_pending:
            self.batch_pending=[]
            self.batch_active=False
            self.suite_button.configure(state='normal')
            self.status.set('Suite stopped.' if self.cancel.is_set() else 'Suite complete. Report: '+str(self.batch_report))
            return
        case=self.batch_pending.pop(0)
        self.acceptance_case=case
        self.case_choice.set(case)
        self.taskbox.delete('1.0','end');self.taskbox.insert('1.0',CASES[case][1])
        self.start()

    def stop(self):
        self.batch_pending=[]
        super().stop()

    def show_controller(self):
        if self.batch_active:
            self.batch_results.append(summarize(self.acceptance_case,self.records,str(self.log_path)))
            self.batch_report.write_text(json.dumps({'cases':self.batch_results},indent=2),encoding='utf-8')
            if any('control returned to the user' in row.get('reason','').lower() for row in self.records):
                self.cancel.set()
        self.suite_button.configure(state='normal' if not self.batch_pending else 'disabled')
        self.start_button.configure(state='normal')
        self.window.geometry('1100x500')
        self.window.deiconify()
        if self.batch_active:self.window.after(800,self.next_suite_case)

    def flush(self):
        self.log_path.write_text(json.dumps({'scope':'primary Windows desktop preview',
            'real_windows_input':True,'records':self.records},indent=2),encoding='utf-8')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--task',help='Prepopulate a task; does not start desktop control')
    parser.add_argument('--acceptance-case',choices=sorted(CASES),help='Use an explicit task with independent outcome checks')
    parser.add_argument('--batch',action='store_true',help='Run bounded acceptance cases once the model is ready')
    parser.add_argument('--suite-cases',nargs='+',choices=sorted(CASES),help='Optional subset for batch runs')
    args=parser.parse_args()
    if args.task and args.acceptance_case:parser.error('Choose --task or --acceptance-case')
    ROOT.mkdir(parents=True,exist_ok=True)
    Preview(CASES[args.acceptance_case][1] if args.acceptance_case else args.task,args.acceptance_case,args.batch,args.suite_cases).window.mainloop()
