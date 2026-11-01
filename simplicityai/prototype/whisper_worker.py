"""Local CPU Whisper dictation, opt-in microphone, no audio saved or uploaded."""
import json
import os
from pathlib import Path
import queue
import sys
import time
import io
import wave


def emit(state, message, **extra):
    print(json.dumps({'state':state,'message':message,**extra}),flush=True)


def main():
    assets=Path(sys.argv[1]);mode=sys.argv[2]
    if mode not in {'Probe','Listen','Level'}: raise ValueError('Unsupported mode')
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
    model=None if mode=='Level' else WhisperModel(str(assets/'models'/'small.en'),device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,local_files_only=True)
    rate=int(device['default_samplerate'])
    blocks=queue.Queue(maxsize=250)
    def callback(data, frames, timing, status):
        try: blocks.put_nowait(data.copy())
        except queue.Full: pass
    chunks=[];voiced=False;silence=0;maximum=0;last_update=0
    with sd.InputStream(samplerate=rate,channels=1,dtype='float32',blocksize=max(1,rate//10),callback=callback):
        started=time.monotonic()
        emit('listening','Listening for up to twenty seconds. Speak naturally, then pause. Stop cancels capture.')
        while time.monotonic()-started<22:
            try: block=blocks.get(timeout=.5)
            except queue.Empty: continue
            energy=float(np.sqrt(np.mean(block*block)))
            maximum=max(maximum,energy)
            if time.monotonic()-last_update>.5:
                level=min(100,round(energy*2000,1))
                emit('listening',f'Listening — microphone level {level}%. Speak, then pause.',mic_level=level,device=device['name'],sample_rate=rate)
                last_update=time.monotonic()
            if mode=='Level' and time.monotonic()-started>=5:break
            if energy>.0012:
                voiced=True;silence=0
            elif voiced: silence+=len(block)/rate
            chunks.append(block[:,0])
            if voiced and silence>=1.4: break
            if not voiced and time.monotonic()-started>10: break
    limited=time.monotonic()-started>=22
    if mode=='Level':
        emit('ready',f"Microphone test complete. Highest level: {min(100,round(maximum*2000,1))}%. Device: {device['name']}. No audio saved or sent to the model.",peak_rms=maximum,sample_rate=rate)
        return
    if not voiced:
        emit('no_speech',f'No clear microphone signal detected. Highest level: {min(100,round(maximum*2000,1))}%. Try Test microphone in Connection and voice status, or type instead.')
        return
    emit('listening','Transcribing locally. The microphone is now closed…')
    audio=np.concatenate(chunks).astype(np.float32)
    encoded=io.BytesIO()
    with wave.open(encoded,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
        wav.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
    encoded.seek(0)
    segments,info=model.transcribe(encoded,language='en',beam_size=3,best_of=1,
                condition_on_previous_text=False,vad_filter=False,no_speech_threshold=.6)
    text=' '.join(segment.text.strip() for segment in segments if segment.no_speech_prob<.7).strip()
    if text: emit('transcribed','Your message was transcribed locally.',text=text[:1800],review_required=limited)
    else: emit('no_speech','No clear words were recognized. Try again or type your message.')


if __name__=='__main__':
    try: main()
    except Exception as error:
        emit('unavailable','Local voice input could not start. Check the microphone connection and permissions; typing still works.',detail=type(error).__name__+': '+str(error)[:400])
