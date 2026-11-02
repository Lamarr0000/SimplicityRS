"""Pilot-owned browser worker. Private pipes, bounded requests, kill on cancellation."""
import json
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid
from server_job import guard_server

RUNTIME=Path('C:/SimplicityAI-Lab/ControlAdapter/.venv/Scripts/python.exe')
WORKER=Path(__file__).resolve().parent.parent/'visual-agent/owned_browser_worker.py'


class BrowserToolError(ValueError):
    def __init__(self,message,may_have_acted,closed_before_action=False):
        super().__init__(message)
        self.may_have_acted=may_have_acted
        self.closed_before_action=closed_before_action


class OwnedBrowser:
    def __init__(self,fixture=False):
        self.fixture=fixture
        self.process=None
        self.guard=None
        self.lock=threading.RLock()
        self.responses=queue.Queue(maxsize=4)
        self.reader=None

    def _start(self):
        if self.process is not None:
            if self.process.poll() is not None:raise RuntimeError('Owned browser exited; open a new browser session')
            return
        if not RUNTIME.is_file():raise RuntimeError('The isolated controlled-browser runtime is missing')
        self.responses=queue.Queue(maxsize=4)
        args=[str(RUNTIME),str(WORKER)]+(['--fixture'] if self.fixture else [])
        self.process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        self.guard=guard_server(self.process)
        process=self.process
        responses=self.responses
        def read():
            try:
                for line in process.stdout:
                    if len(line)>128000:raise ValueError('Browser response exceeds limit')
                    responses.put_nowait(json.loads(line))
            except Exception as error:
                try:responses.put_nowait(error)
                except queue.Full:pass
            finally:
                try:responses.put_nowait(EOFError('Owned browser closed'))
                except queue.Full:pass
        self.reader=threading.Thread(target=read,daemon=True)
        self.reader.start()

    def call(self,op,args,check,_recover=True):
        with self.lock:
            try:
                check()
                if self.process is None and op!='open':
                    raise ValueError('Open the owned browser before observing or acting')
                if op=='open' and self.process is not None and self.process.poll() is not None:
                    self.close()
                self._start()
                request_id=uuid.uuid4().hex
                data=json.dumps({'id':request_id,'op':op,'args':args})+'\n'
                if len(data)>32000:raise ValueError('Browser request exceeds limit')
                self.process.stdin.write(data);self.process.stdin.flush()
                deadline=time.monotonic()+45
                while time.monotonic()<deadline:
                    check()
                    try:response=self.responses.get(timeout=.1)
                    except queue.Empty:continue
                    if isinstance(response,Exception):raise response
                    if response.get('id')!=request_id:raise RuntimeError('Stale browser response; request not replayed')
                    result=response['result']
                    if result.get('error'):raise BrowserToolError(result['error'],result.get('may_have_acted',True),result.get('closed_before_action',False))
                    return result
                raise TimeoutError('Owned browser request timed out; action outcome unknown')
            except BrowserToolError as error:
                if op=='open' and _recover and error.closed_before_action and not error.may_have_acted:
                    self.close()
                    return self.call(op,args,check,_recover=False)
                if error.may_have_acted:self.close()
                raise
            except BaseException:
                self.close()
                raise

    def close(self):
        process=self.process
        self.process=None
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        if self.guard:self.guard();self.guard=None
        if process is not None:
            for stream in (process.stdin,process.stdout):
                try:stream.close()
                except (OSError,ValueError):pass
