"""User-invoked pilot launcher; owns only its new server/window process trees."""
import json
import argparse
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
ASSETS=Path('C:/SimplicityAI-Lab/StreamingPrototype')
sys.path.insert(0,'C:/SimplicityAI-Lab/ThemHands')
from voice import _guard_process


def request(path,token=None):
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req=urllib.request.Request('http://127.0.0.1:8770'+path,
        data=b'{}' if token else None,headers={'X-ThemHands-Token':token} if token else {})
    with opener.open(req,timeout=3) as response:return json.load(response)


def main(model='gpt-oss:20b'):
    # Fail on any occupied port; never attach to or stop another process.
    with socket.socket() as probe:probe.bind(('127.0.0.1',8770))
    (ASSETS/'logs').mkdir(exist_ok=True)
    server=None;guard=None
    try:
        with (ASSETS/'logs/server.log').open('ab') as output:
            server=subprocess.Popen([sys.executable,str(ROOT/'server.py'),'--model',model],cwd=ROOT,
                stdout=output,stderr=output,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        guard=_guard_process(server)
        for _ in range(80):
            if server.poll() is not None:raise RuntimeError('Prototype did not start; see StreamingPrototype/logs/server.log')
            try:
                if request('/health').get('app')=='SimplicityAI-streaming':break
            except OSError:pass
            time.sleep(.25)
        else:raise RuntimeError('Prototype startup timed out')
        url=(ROOT/'session-url.txt').read_text(encoding='utf-8').strip()
        (ASSETS/'session-url.txt').write_text(url,encoding='utf-8')
        startup=subprocess.STARTUPINFO();startup.dwFlags=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=1
        window=subprocess.Popen([str(ASSETS/'window-runtime/SimplicityAI.exe')],startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
        window_guard=_guard_process(window)
        try:window.wait()
        finally:window_guard()
    finally:
        if server is not None and server.poll() is None:
            try:request('/shutdown',url.split('#',1)[1]);server.wait(timeout=5)
            except (OSError,ValueError,UnboundLocalError,subprocess.TimeoutExpired):
                server.terminate();server.wait(timeout=5)
        if guard:guard()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['gpt-oss:20b','qwen3:8b'],default='gpt-oss:20b')
    main(parser.parse_args().model)
