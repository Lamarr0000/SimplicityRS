"""One fixed Kokoro voice, warm CPU worker, no persistent audio files."""
import base64
from pathlib import Path
import json
import subprocess
import threading
from voice import _guard_process

ROOT = Path(__file__).resolve().parent


class KokoroSpeech:
    def __init__(self):
        self.lock = threading.RLock()
        self.process = None
        self.guard = None
        self.busy = False
        self.last_error = ''

    def stop(self):
        with self.lock:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait()
                self.process = None
            if self.guard:
                self.guard()
                self.guard = None

    def cancel(self):
        """Cancel active synthesis, retaining an idle worker for the next reply."""
        with self.lock:
            if self.busy:
                self.stop()

    def synthesize(self, text):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 2000:
            raise ValueError('Please read a shorter reply (up to 2000 characters).')
        assets = ROOT / 'kokoro'
        if not assets.is_dir():
            assets = ROOT.parent / 'Kokoro'  # Host development layout only.
        runtime = assets / 'python' / 'cpython-3.12.16-windows-x86_64-none' / 'python.exe'
        if not runtime.is_file():
            raise ValueError('Kokoro playback files are missing. The on-screen text is still available.')
        with self.lock:
            if self.busy:
                raise ValueError('A voice reply is already being prepared. Stop it first.')
            if self.process is None or self.process.poll() is not None:
                self.stop()
                self.process = subprocess.Popen([str(runtime), str(ROOT / 'kokoro_worker.py'), str(assets)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    self.guard = _guard_process(self.process)
                except Exception:
                    self.stop()
                    raise ValueError('Local voice process could not be secured. Text remains available.')
            process = self.process
            self.busy = True
            self.last_error = ''
        expired = threading.Event()
        def timeout():
            expired.set()
            with self.lock:
                if self.process is process:
                    self.stop()
        timer = threading.Timer(90, timeout)
        timer.daemon = True
        timer.start()
        try:
            process.stdin.write(json.dumps({'text': text.strip()}).encode('utf-8')+b'\n')
            process.stdin.flush()
            value = json.loads(process.stdout.readline(24_000_000))
            if value.get('error'):
                self.last_error=value['error']
                raise ValueError('Voice worker initialization failed')
            audio = base64.b64decode(value['audio'], validate=True)
            if not audio.startswith(b'RIFF') or audio[8:12] != b'WAVE':
                raise ValueError('Invalid voice output')
            with self.lock:
                if self.process is not process or expired.is_set():
                    raise ValueError('Playback stopped')
            return audio
        except Exception as error:
            if not self.last_error:self.last_error=type(error).__name__+': '+str(error)[:400]
            with self.lock:
                if self.process is process:
                    self.stop()
            raise ValueError('Voice preparation stopped or did not finish. Please use the text or try a shorter reply.')
        finally:
            timer.cancel()
            with self.lock:
                self.busy = False
