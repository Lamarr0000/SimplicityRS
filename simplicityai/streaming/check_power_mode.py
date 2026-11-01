"""One identical synthetic case after a user-selected power mode. Read-only."""
import ctypes
import json
import subprocess
import threading
import time
import uuid

from compare_models import api, run_case, CASES
from server import ASSETS


def main():
    result={'settings_changed_by_script':False,'model':'qwen3:8b','thinking':False,'gpu_samples':[]}
    raw=(ctypes.c_ubyte*16)();fn=ctypes.WinDLL('powrprof').PowerGetEffectiveOverlayScheme
    fn.argtypes=[ctypes.c_void_p];fn.restype=ctypes.c_ulong
    result['overlay_return_code']=fn(ctypes.byref(raw))
    result['effective_overlay_guid']=str(uuid.UUID(bytes_le=bytes(raw)))
    result['before']=subprocess.check_output(['nvidia-smi','-q','-d','PERFORMANCE,CLOCK,POWER'],text=True)
    done=threading.Event()
    def sample():
        while not done.is_set():
            value=subprocess.run(['nvidia-smi','--query-gpu=pstate,clocks.current.sm,clocks.current.memory,power.draw,temperature.gpu,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True)
            result['gpu_samples'].append({'utc':time.time(),'readings':value.stdout.strip()})
            done.wait(1)
    watcher=threading.Thread(target=sample,daemon=True);watcher.start()
    try:
        api('/api/chat',{'model':'qwen3:8b','messages':[],'think':False,'stream':False,
                         'keep_alive':'15m','options':{'num_ctx':8192}})
        result['warmup']=run_case('qwen3:8b',{},*CASES[0])
        print('Warmup finished',flush=True)
        result['measured']=run_case('qwen3:8b',{},*CASES[1])
        result['under_load_end']=subprocess.check_output(['nvidia-smi','-q','-d','PERFORMANCE,CLOCK,POWER'],text=True)
    finally:
        done.set();watcher.join(timeout=5)
        api('/api/chat',{'model':'gpt-oss:20b','messages':[],'stream':False,'keep_alive':'30m',
                         'think':'low','options':{'num_ctx':8192}})
        result['restored']=api('/api/ps')
        (ASSETS/'logs/power-mode-comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    measured=result['measured'];metrics=[e['metrics'] for e in measured['events'] if e['type']=='model.timing']
    print(json.dumps({'overlay':result['effective_overlay_guid'],'seconds':measured['seconds'],
        'first_segment_seconds':measured['first_segment_seconds'],'reply':measured['reply'],
        'error':measured['error'],'metrics':metrics,'gpu_samples':result['gpu_samples']},indent=2))


if __name__=='__main__':main()
