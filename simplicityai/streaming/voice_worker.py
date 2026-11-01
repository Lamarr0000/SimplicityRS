"""Continuous 16 kHz PCM -> Silero VAD -> online Zipformer. No mic or network."""
import base64
from collections import deque
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import wave


class Gate:
    def __init__(self):self.reset()
    def reset(self):self.pre=deque(maxlen=16);self.active=False;self.positive=0;self.quiet=0;self.frames=0
    def feed(self,frame,probability):
        self.pre.append(frame)
        if not self.active:
            self.positive=self.positive+1 if probability>=.55 else 0
            if self.positive>=3:
                self.active=True;self.frames=len(self.pre);self.quiet=0
                return 'start',list(self.pre),False
            return None,[],False
        self.frames+=1;self.quiet=self.quiet+1 if probability<.35 else 0
        if self.quiet>=20 or self.frames>=782:
            limited=self.frames>=782;self.active=False;self.positive=self.quiet=0
            return 'end',[frame],limited
        return 'frame',[frame],False


class Recognizer:
    def __init__(self,assets,legacy):
        sys.path.insert(0,str(assets/'speech-deps'));sys.path.insert(0,str(legacy))
        import numpy as np
        import onnxruntime as ort
        import sherpa_onnx
        from zipformer_worker import ShortWordFallback
        self.np=np;self.fallback=ShortWordFallback(legacy.parent/'SpeechConversation')
        ort.disable_telemetry_events();options=ort.SessionOptions()
        options.intra_op_num_threads=1;options.inter_op_num_threads=1
        self.vad=ort.InferenceSession(str(assets/'models/silero-vad.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        model=legacy.parent/'SpeechStreaming/models/zipformer20230626'
        self.asr=sherpa_onnx.OnlineRecognizer.from_transducer(tokens=str(model/'tokens.txt'),
            encoder=str(model/'encoder-epoch-99-avg-1-chunk-16-left-128.int8.onnx'),
            decoder=str(model/'decoder-epoch-99-avg-1-chunk-16-left-128.onnx'),
            joiner=str(model/'joiner-epoch-99-avg-1-chunk-16-left-128.int8.onnx'),
            num_threads=2,provider='cpu',decoding_method='greedy_search',enable_endpoint_detection=False)
        self.reset()

    def reset(self):
        np=self.np;self.context=np.zeros((1,64),dtype=np.float32)
        self.state=np.zeros((2,1,128),dtype=np.float32);self.gate=Gate()
        self.stream=None;self.audio=[];self.previous='';self.frame_index=0

    def feed(self,pcm):
        if len(pcm)!=1024:raise ValueError('Expected exactly 512 mono PCM16 samples')
        np=self.np;frame=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
        inputs=np.concatenate((self.context,frame.reshape(1,-1)),axis=1)
        probability,self.state=self.vad.run(None,{'input':inputs,'state':self.state,'sr':np.array(16000,dtype=np.int64)})
        self.context=inputs[:,-64:];phase,frames,limited=self.gate.feed(pcm,float(probability.reshape(-1)[0]))
        events=[];self.frame_index+=1
        if phase=='start':
            self.stream=self.asr.create_stream();self.audio=[];self.previous=''
            self.stream.accept_waveform(16000,np.zeros(12800,dtype=np.float32))
            events.append({'type':'speech.start'})
        if self.stream is not None and phase:
            for data in frames:
                self.audio.append(data)
                self.stream.accept_waveform(16000,np.frombuffer(data,dtype='<i2').astype(np.float32)/32768)
            while self.asr.is_ready(self.stream):self.asr.decode_stream(self.stream)
            text=self.asr.get_result(self.stream).strip()
            if text and text!=self.previous and self.frame_index%3==0:
                self.previous=text;events.append({'type':'transcript.partial','text':text})
        if phase=='end':
            self.stream.accept_waveform(16000,np.zeros(12800,dtype=np.float32));self.stream.input_finished()
            while self.asr.is_ready(self.stream):self.asr.decode_stream(self.stream)
            text=self.asr.get_result(self.stream).strip();backend='zipformer-online'
            from zipformer_worker import verify_short
            if verify_short(text):
                wav=io.BytesIO()
                with wave.open(wav,'wb') as output:
                    output.setnchannels(1);output.setsampwidth(2);output.setframerate(16000);output.writeframes(b''.join(self.audio))
                text=self.fallback.transcribe(wav.getvalue());backend='whisper-short-word-fallback'
            events.append({'type':'transcript.final','text':text,'limited':limited,'backend':backend})
            self.stream=None;self.audio=[];self.previous=''
        return events


def main():
    os.environ['HF_HUB_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    with contextlib.redirect_stdout(sys.stderr):recognizer=Recognizer(Path(sys.argv[1]),Path(sys.argv[2]))
    print('{"ready":true}',flush=True)
    try:
        while True:
            line=sys.stdin.buffer.readline(10001)
            if not line:break
            if len(line)>10000:raise ValueError('Oversized voice frame')
            value=json.loads(line)
            with contextlib.redirect_stdout(sys.stderr):
                if value.get('op')=='reset':recognizer.reset();events=[]
                elif value.get('op')=='frame':events=recognizer.feed(base64.b64decode(value['pcm'],validate=True))
                else:raise ValueError('Unknown audio operation')
            print(json.dumps({'events':events}),flush=True)
    finally:recognizer.fallback.close()


if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'error':type(error).__name__+': '+str(error)[:300]}),flush=True)
