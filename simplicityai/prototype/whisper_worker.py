"""Local CPU Whisper dictation, opt-in microphone, no audio saved or uploaded."""
import json
import os
from pathlib import Path
import queue
import sys
import time


def emit(state, message, **extra):
    print(json.dumps({'state':state,'message':message,**extra}),flush=True)


def main():
    assets=Path(sys.argv[1]);mode=sys.argv[2]
    if mode not in {'Probe','Listen'}: raise ValueError('Unsupported mode')
    sys.path.insert(0,str(assets/'deps'))
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    import numpy as np
    import sounddevice as sd
    from faster_whisper import WhisperModel
    if not (assets/'models'/'small.en'/'model.bin').is_file(): raise ValueError('Model missing')
    device=sd.query_devices(kind='input')
    if device['max_input_channels']<1: raise ValueError('No input channels')
    if mode=='Probe':
        emit('ready','Local Whisper files and an input device are available. Click Talk when ready to test recognition.')
        return
    model=WhisperModel(str(assets/'models'/'small.en'),device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
    blocks=queue.Queue(maxsize=250)
    def callback(data, frames, timing, status):
        try: blocks.put_nowait(data.copy())
        except queue.Full: pass
    chunks=[];voiced=False;silence=0;started=time.monotonic()
    with sd.InputStream(samplerate=16000,channels=1,dtype='float32',blocksize=1600,callback=callback):
        emit('listening','Listening for up to twenty seconds. Speak naturally, then pause. Stop cancels capture.')
        while time.monotonic()-started<22:
            try: block=blocks.get(timeout=.5)
            except queue.Empty: continue
            energy=float(np.sqrt(np.mean(block*block)))
            if energy>.004:
                voiced=True;silence=0
            elif voiced: silence+=len(block)/16000
            chunks.append(block[:,0])
            if voiced and silence>=1.4: break
            if not voiced and time.monotonic()-started>10: break
    limited=time.monotonic()-started>=22
    if not voiced:
        emit('no_speech','I did not catch a clear voice. Click Talk to try again, or type your message.')
        return
    emit('listening','Transcribing locally. The microphone is now closed…')
    audio=np.concatenate(chunks).astype(np.float32)
    segments,info=model.transcribe(audio,language='en',beam_size=3,best_of=1,
                condition_on_previous_text=False,vad_filter=False,no_speech_threshold=.6)
    text=' '.join(segment.text.strip() for segment in segments if segment.no_speech_prob<.7).strip()
    if text: emit('transcribed','Your message was transcribed locally.',text=text[:1800],review_required=limited)
    else: emit('no_speech','No clear words were recognized. Try again or type your message.')


if __name__=='__main__':
    try: main()
    except Exception:
        emit('unavailable','Local voice input could not start. Check the microphone connection and permissions; typing still works.')
