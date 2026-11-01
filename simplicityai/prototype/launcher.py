"""Open the local ThemHands UI, starting its server when needed."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import urllib.error
import webbrowser

ROOT = Path(__file__).resolve().parent
HEALTH = "http://127.0.0.1:8769/health"


def ready():
    try:
        with urllib.request.urlopen(HEALTH, timeout=2) as response:
            return json.load(response).get("app") == "ThemHands"
    except (OSError, ValueError):
        return False


if not ready():
    (ROOT / "logs").mkdir(exist_ok=True)
    with (ROOT / "logs" / "server.log").open("ab") as output:
        subprocess.Popen([sys.executable, str(ROOT / "app.py")], cwd=ROOT,
                         stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(30):
        if ready() and (ROOT / "session-url.txt").exists():
            break
        time.sleep(.5)
    else:
        raise RuntimeError("ThemHands did not start. See logs/server.log.")

url = (ROOT / "session-url.txt").read_text(encoding="utf-8").strip()
if not url.startswith("http://127.0.0.1:8769/#"):
    raise RuntimeError("Invalid local session URL")
session_token=url.split('#',1)[1]
request=urllib.request.Request('http://127.0.0.1:8769/chat/reset',data=b'{}',
            headers={'X-ThemHands-Token':session_token,'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request,timeout=8) as response:
        json.load(response)
except urllib.error.HTTPError as error:
    if error.code==400:
        raise RuntimeError('An earlier task is still running. Stop or finish it before opening a fresh session.') from error
    raise
edge = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe"
if edge.is_file():
    subprocess.Popen([str(edge), "--new-window", url], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
else:
    webbrowser.open(url)
