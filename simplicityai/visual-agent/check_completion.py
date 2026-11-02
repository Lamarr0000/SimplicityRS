"""Read-only local inference replay. Never imports an input driver or sends UI input."""
import base64
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
from PIL import Image
from agent_context import AgentContext
from desktop_actions import decode
from probe import ROOT

TASK='In the blank Untitled Notepad document, type Offline visual control test. Do not save, close, or edit other tabs. Finish when that exact sentence is visible.'


def main():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://127.0.0.1:11434/api/ps',timeout=2) as response:
            models=json.load(response).get('models',[])
        if any(model.get('size_vram',0)>1024**3 for model in models):
            raise RuntimeError('Competing Ollama GPU model; no automatic unload')
    except urllib.error.URLError:pass
    with socket.socket() as probe:probe.bind(('127.0.0.1',8772))
    key=secrets.token_urlsafe(32)
    env=dict(os.environ,LLAMA_API_KEY=key)
    args=[str(ROOT/'runtime/llama-server.exe'),'-m',str(ROOT/'UI-TARS-1.5-7B.Q4_K_M.gguf'),
          '--mmproj',str(ROOT/'UI-TARS-1.5-7B.mmproj-f16.gguf'),'--host','127.0.0.1',
          '--port','8772','--alias','ui-tars','-c','4096','-ngl','99','-t','6',
          '--parallel','1','--image-min-tokens','1024']
    server=None
    def request(path,data=None):
        headers={'Authorization':'Bearer '+key}
        if data is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request('http://127.0.0.1:8772'+path,
            None if data is None else json.dumps(data).encode(),headers)
        with opener.open(req,timeout=90) as response:return json.load(response)
    results=[]
    try:
        with (ROOT/'completion-replay-server.log').open('ab') as output:
            server=subprocess.Popen(args,env=env,stdout=output,stderr=output,
                stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            if server.poll() is not None:raise RuntimeError('Model exited during startup')
            try:
                if request('/health').get('status')=='ok':break
            except (OSError,ValueError):pass
            time.sleep(.5)
        else:raise TimeoutError('Startup timed out')
        cases=[('complete-original','completed-notepad-replay.png',TASK,True),
               ('blank-original','blank-notepad-replay.png',TASK,False),
               ('complete-keep-open','completed-notepad-replay.png',
                'Enter Offline visual control test in Notepad. Leave the document and window open. Stop once the text is present.',True),
               ('blank-keep-open','blank-notepad-replay.png',
                'Enter Offline visual control test in Notepad. Leave the document and window open. Stop once the text is present.',False)]
        for name,filename,task,expected in cases:
            image=Image.open(ROOT/filename).convert('RGB').resize((1288,672))
            buf=io.BytesIO();image.save(buf,'PNG')
            context=AgentContext(task)
            messages=context.observation('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(),
                'Read-only replay: choose the next action from the current screen.',
                'Notepad')
            start=time.perf_counter()
            result=request('/v1/chat/completions',{'model':'ui-tars','messages':messages,
                'temperature':0,'max_tokens':256})
            output=result['choices'][0]['message']['content'].strip()
            row={'case':name,'expected_finished':expected,'seconds':round(time.perf_counter()-start,3),
                 'output':output,'real_ui_input':False}
            try:
                action=decode(output,*image.size)
                row.update(kind=action['kind'],passed=(action['kind']=='finished')==expected)
            except (ValueError,SyntaxError) as error:row.update(passed=False,error=str(error))
            results.append(row)
            (ROOT/'completion-replay-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(json.dumps(row),flush=True)
        return 0 if all(row['passed'] for row in results) else 1
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)


if __name__=='__main__':raise SystemExit(main())
