"""Owned warm recognizer for opt-in browser capture, with bounded in-memory audio."""
import base64
import io
import json
from pathlib import Path
import subprocess
import threading
import wave
from voice import _guard_process

ROOT=Path(__file__).resolve().parent
MAX_AUDIO=11_000_000


def worker_configuration():
    whisper=ROOT/'whisper'
    if not whisper.is_dir():whisper=ROOT.parent/'SpeechConversation'
    assets=ROOT/'streaming-asr'
    if not assets.is_dir():assets=ROOT.parent/'SpeechStreaming'
    marker=assets/'backend.json'
    runtime=whisper/'python/cpython-3.12.16-windows-x86_64-none/python.exe'
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8'))!={'schema':1,'backend':'zipformer20230626'}:
            raise ValueError('Unknown local speech backend configuration')
        own_runtime=assets/'python/cpython-3.12.16-windows-x86_64-none/python.exe'
        if own_runtime.is_file():runtime=own_runtime
        return runtime,[str(ROOT/'zipformer_worker.py'),str(assets),str(whisper)]
    return runtime,[str(ROOT/'stream_asr_worker.py'),str(whisper)]


def validate_audio(audio):
    if not isinstance(audio,bytes) or not 44<=len(audio)<=MAX_AUDIO:
        raise ValueError('Invalid microphone audio size')
    try:
        with wave.open(io.BytesIO(audio),'rb') as wav:
            if wav.getnchannels()!=1 or wav.getsampwidth()!=2 or not 8000<=wav.getframerate()<=192000 or wav.getcomptype()!='NONE':
                raise ValueError('Expected uncompressed mono PCM microphone audio')
            frames=wav.getnframes()
            if not .15<=frames/wav.getframerate()<=26:
                raise ValueError('Speak a phrase between a fraction of a second and twenty-five seconds')
            if len(wav.readframes(frames))!=frames*2:
                raise ValueError('Microphone audio was incomplete')
    except (wave.Error,EOFError) as error:
        raise ValueError('Invalid WAV microphone audio') from error


class StreamASR:
    def __init__(self):
        self.lock=threading.RLock()
        self.operation=threading.Lock()
        self.process=None
        self.guard=None
        self.ready=False
        self.busy=False
        self.generation=0
        self.backend='whisper-cpu'

    def stop(self):
        with self.lock:
            self.generation+=1
            if self.process is not None and self.process.poll() is None:
                self.process.terminate();self.process.wait()
            self.process=None;self.ready=False
            if self.guard:self.guard();self.guard=None

    def cancel(self):
        with self.lock:
            if self.busy:self.stop()

    def run(self,audio=None):
        if audio is not None:validate_audio(audio)
        with self.lock:generation=self.generation
        if not self.operation.acquire(timeout=90):raise ValueError('Speech recognition is busy')
        timer=None
        try:
            with self.lock:
                if generation!=self.generation:raise ValueError('Speech recognition cancelled')
                self.busy=True
                if self.process is None or self.process.poll() is not None:
                    runtime,arguments=worker_configuration()
                    if not runtime.is_file():raise ValueError('Local speech recognition files are missing')
                    self.ready=False
                    self.process=subprocess.Popen([str(runtime),*arguments],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
                    self.guard=_guard_process(self.process)
                process=self.process
            timer=threading.Timer(90,self.stop);timer.daemon=True;timer.start()
            if not self.ready:
                value=json.loads(process.stdout.readline(16000000))
                if value.get('ready') is not True:raise ValueError('Speech recognizer did not initialize')
                with self.lock:
                    if self.process is not process:raise ValueError('Speech recognition cancelled')
                    self.ready=True
                    self.backend=value.get('backend','whisper-cpu')
            if audio is None:return {'ready':True,'backend':self.backend}
            process.stdin.write(json.dumps({'audio':base64.b64encode(audio).decode('ascii')}).encode()+b'\n');process.stdin.flush()
            result=json.loads(process.stdout.readline(16000000))
            if not isinstance(result.get('text'),str):raise ValueError('Speech recognition did not produce text')
            with self.lock:
                if self.process is not process:raise ValueError('Speech recognition cancelled')
            return {'text':result['text'][:1800],'backend':result.get('backend',self.backend)}
        except Exception as error:
            with self.lock:
                if generation==self.generation:self.stop()
            raise ValueError('Local speech recognition stopped or failed. You can type instead.') from error
        finally:
            if timer:timer.cancel()
            with self.lock:self.busy=False
            self.operation.release()
