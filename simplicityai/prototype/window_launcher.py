"""Own the dedicated Windows window and exact local server process tree."""
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from voice import _guard_process

ROOT = Path(__file__).resolve().parent


def request(path, token=None, data=None):
    headers = {'X-ThemHands-Token': token} if token else {}
    req = urllib.request.Request('http://127.0.0.1:8769' + path,
        data=json.dumps(data).encode() if data is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=3) as response:
        return json.load(response)


def launch():
    assets = ROOT / 'window-runtime'
    if not all((assets / name).is_file() for name in (
            'SimplicityAI.exe', 'Microsoft.Web.WebView2.Core.dll', 'Microsoft.Web.WebView2.WinForms.dll', 'WebView2Loader.dll')):
        raise RuntimeError('App window components are missing. Install the App Window update first.')
    try:
        healthy = request('/health')
    except OSError:
        healthy = None
    if healthy:
        raise RuntimeError('SimplicityAI is already running. Use its existing window or stop it before reopening.')
    (ROOT / 'logs').mkdir(exist_ok=True)
    guard = None
    server = None
    try:
        with (ROOT / 'logs' / 'server.log').open('ab') as output:
            server = subprocess.Popen([sys.executable, str(ROOT / 'app.py')], cwd=ROOT,
                stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                creationflags=subprocess.CREATE_NO_WINDOW)
        guard = _guard_process(server)
        for _ in range(60):
            if server.poll() is not None:
                raise RuntimeError('Local service did not start. See logs/server.log.')
            try:
                if request('/health').get('app') == 'ThemHands':
                    break
            except OSError:
                pass
            time.sleep(.25)
        else:
            raise RuntimeError('Local service startup timed out.')
        startup = subprocess.STARTUPINFO()
        startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 1  # Show the app even when started by a hidden shortcut.
        shell = subprocess.Popen([str(assets / 'SimplicityAI.exe')], cwd=ROOT, startupinfo=startup,
            creationflags=subprocess.CREATE_NO_WINDOW)
        shell_guard = _guard_process(shell)
        try:
            shell.wait()
        finally:
            shell_guard()
    finally:
        if server is not None and server.poll() is None:
            try:
                token = (ROOT / 'session-url.txt').read_text().strip().split('#', 1)[1]
                request('/shutdown', token, {})
                server.wait(timeout=5)
            except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
                server.terminate()
                server.wait(timeout=5)
        if guard:
            guard()  # Kills only descendants of our server, including collectors.


if __name__ == '__main__':
    launch()
