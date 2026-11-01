"""CPU recognizer with a lazy, separately isolated Whisper short-word fallback.

Accepts bounded WAV messages on stdin. Never opens a microphone or network.
The application owns this process and descendants in a kill-on-close job.
"""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import wave
from stream_asr import validate_audio


def verify_short(text):
    words=text.strip().lower().split()
    return len(words)==1 and words[0] not in {
        'stop','cancel','yes','no','okay','ok','hello','hi','thanks'}


class ShortWordFallback:
    def __init__(self, assets):
        self.assets=assets
        self.process=None

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate();self.process.wait()
            self.process=None

    def transcribe(self, audio):
        if self.process is None or self.process.poll() is not None:
            runtime=self.assets/'python/cpython-3.12.16-windows-x86_64-none/python.exe'
            self.process=subprocess.Popen([str(runtime),str(Path(__file__).with_name('stream_asr_worker.py')),str(self.assets)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            ready=json.loads(self.process.stdout.readline(16000000))
            if ready.get('ready') is not True:raise ValueError('Whisper fallback unavailable')
        self.process.stdin.write(json.dumps({'audio':base64.b64encode(audio).decode('ascii')}).encode()+b'\n')
        self.process.stdin.flush()
        value=json.loads(self.process.stdout.readline(16000000))
        if not isinstance(value.get('text'),str):raise ValueError('Whisper fallback failed')
        return value['text'][:1800]


def recognize(recognizer, np, audio):
    validate_audio(audio)
    with wave.open(io.BytesIO(audio),'rb') as wav:
        rate=wav.getframerate()
        samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
    stream=recognizer.create_stream()
    # Numeric silence flushes model context; no real-time sleep is added.
    stream.accept_waveform(rate,np.zeros(int(rate*.8),dtype=np.float32))
    stream.accept_waveform(rate,samples)
    stream.accept_waveform(rate,np.zeros(int(rate*.8),dtype=np.float32))
    stream.input_finished()
    while recognizer.is_ready(stream):recognizer.decode_stream(stream)
    return recognizer.get_result(stream).strip()


def main():
    assets=Path(sys.argv[1]);whisper=Path(sys.argv[2])
    sys.path.insert(0,str(assets/'deps'))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    with contextlib.redirect_stdout(sys.stderr):
        import numpy as np
        import sherpa_onnx
        model=assets/'models/zipformer20230626'
        recognizer=sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=str(model/'tokens.txt'),
            encoder=str(model/'encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx'),
            decoder=str(model/'decoder-epoch-99-avg-1-chunk-16-left-128.onnx'),
            joiner=str(model/'joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx'),
            num_threads=2,decoding_method='greedy_search',provider='cpu',enable_endpoint_detection=False)
    fallback=ShortWordFallback(whisper)
    print(json.dumps({'ready':True,'backend':'zipformer-cpu'}),flush=True)
    try:
        while True:
            line=sys.stdin.buffer.readline(16000001)
            if not line:break
            if len(line)>16000000:raise ValueError('Audio request too large')
            value=json.loads(line)
            audio=base64.b64decode(value['audio'],validate=True)
            with contextlib.redirect_stdout(sys.stderr):
                text=recognize(recognizer,np,audio)
                backend='zipformer-cpu'
                if verify_short(text):
                    text=fallback.transcribe(audio);backend='whisper-short-word-fallback'
                else:
                    text=text[:1].upper()+text[1:].lower()
            print(json.dumps({'text':text[:1800],'backend':backend}),flush=True)
    finally:
        fallback.close()


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'error':type(error).__name__+': '+str(error)[:300]}),flush=True)
