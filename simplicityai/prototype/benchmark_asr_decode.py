"""Compare local Whisper decoding on supplied synthetic WAV fixtures; no mic."""
import argparse
import base64
import io
import json
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    import os
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    sys.path.insert(0,str(args.assets/'deps'))
    from faster_whisper import WhisperModel
    model=WhisperModel(str(args.assets/'models/small.en'),device='cpu',
        compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
    fixtures=json.loads(args.fixtures.read_text(encoding='utf-8'))
    # Unmeasured warmup, then alternating order avoids always favoring the cache
    # for one decoder. Synthetic clear speech is not a real microphone test.
    list(model.transcribe(io.BytesIO(base64.b64decode(fixtures[0]['audio'])),language='en',beam_size=3)[0])
    results=[]
    for index,fixture in enumerate(fixtures):
        for beam in ((3,1) if index%2==0 else (1,3)):
            start=time.monotonic()
            segments,_=model.transcribe(io.BytesIO(base64.b64decode(fixture['audio'])),
                language='en',beam_size=beam,best_of=1,condition_on_previous_text=False,
                vad_filter=False,no_speech_threshold=.6)
            text=' '.join(s.text.strip() for s in segments if s.no_speech_prob<.7).strip()
            result={'beam_size':beam,'seconds':time.monotonic()-start,
                'expected':fixture['text'],'actual':text}
            results.append(result)
            args.output.write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(json.dumps(result),flush=True)


if __name__=='__main__': main()
