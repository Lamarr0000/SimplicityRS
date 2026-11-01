"""Persistent local recognizer. Receives bounded WAVs on stdin; never opens a mic."""
import base64
import contextlib
import io
import json
import os
from pathlib import Path
import sys


def main():
    assets=Path(sys.argv[1])
    sys.path.insert(0,str(assets/'deps'))
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    with contextlib.redirect_stdout(sys.stderr):
        from faster_whisper import WhisperModel
        model=WhisperModel(str(assets/'models'/'small.en'),device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
    print(json.dumps({'ready':True}),flush=True)
    for line in sys.stdin.buffer:
        if len(line)>16_000_000:raise ValueError('Audio request too large')
        payload=json.loads(line)
        audio=base64.b64decode(payload['audio'],validate=True)
        with contextlib.redirect_stdout(sys.stderr):
            segments,_=model.transcribe(io.BytesIO(audio),language='en',beam_size=3,best_of=1,condition_on_previous_text=False,vad_filter=False,no_speech_threshold=.6)
            text=' '.join(s.text.strip() for s in segments if s.no_speech_prob<.7).strip()
        print(json.dumps({'text':text[:1800]}),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'error':type(error).__name__+': '+str(error)[:300]}),flush=True)
