"""CPU-only streaming-model throughput on synthetic audio. No microphone."""
import argparse
import base64
import io
import json
from pathlib import Path
import sys
import time
import wave


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model-dir',default='zipformer20m',choices=['zipformer20m','zipformer20230626'])
    parser.add_argument('--decoding-method',default='greedy_search',choices=['greedy_search','modified_beam_search'])
    parser.add_argument('--padding',type=float,default=0.0,
                        help='Synthetic silence before/after the clip, seconds (0 to 2)')
    args=parser.parse_args()
    if not 0<=args.padding<=2:parser.error('padding must be between 0 and 2 seconds')
    sys.path.insert(0,str(args.assets/'deps'))
    import numpy as np
    import sherpa_onnx
    model=args.assets/'models'/args.model_dir
    suffix='-chunk-16-left-128' if args.model_dir=='zipformer20230626' else ''
    started=time.monotonic()
    recognizer=sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(model/'tokens.txt'),encoder=str(model/f'encoder-epoch-99-avg-1{suffix}.int8.onnx'),
        decoder=str(model/f'decoder-epoch-99-avg-1{suffix}.onnx'),
        joiner=str(model/f'joiner-epoch-99-avg-1{suffix}.int8.onnx'),num_threads=2,
        decoding_method=args.decoding_method,provider='cpu',enable_endpoint_detection=False)
    load=time.monotonic()-started
    results=[]
    for fixture in json.loads(args.fixtures.read_text(encoding='utf-8')):
        with wave.open(io.BytesIO(base64.b64decode(fixture['audio'])),'rb') as wav:
            if wav.getnchannels()!=1 or wav.getsampwidth()!=2:raise ValueError('Expected mono PCM16')
            rate=wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
        stream=recognizer.create_stream()
        start=time.monotonic();cpu=time.process_time();first_partial=None
        # Explicit boundary-padding experiment for this older streaming model.
        # Retain the unpadded run separately; do not hide clipped-word failures.
        if args.padding:
            stream.accept_waveform(rate,np.zeros(int(rate*args.padding),dtype=np.float32))
            while recognizer.is_ready(stream):recognizer.decode_stream(stream)
        chunk=rate//10
        for offset in range(0,len(samples),chunk):
            stream.accept_waveform(rate,samples[offset:offset+chunk])
            while recognizer.is_ready(stream):recognizer.decode_stream(stream)
            if first_partial is None and recognizer.get_result(stream).strip():
                first_partial=min(offset+chunk,len(samples))/rate
        stream.accept_waveform(rate,np.zeros(int(rate*max(.3,args.padding)),dtype=np.float32))
        stream.input_finished()
        while recognizer.is_ready(stream):recognizer.decode_stream(stream)
        elapsed=time.monotonic()-start
        result={'expected':fixture['text'],'actual':recognizer.get_result(stream),
                'audio_seconds':len(samples)/rate,'compute_seconds':elapsed,
                'cpu_seconds':time.process_time()-cpu,'real_time_factor':elapsed/(len(samples)/rate),
                'leading_padding_seconds':args.padding,
                'trailing_padding_seconds':max(.3,args.padding),
                'first_partial_after_input_seconds':first_partial}
        results.append(result)
        args.output.write_text(json.dumps({'runtime':sherpa_onnx.__version__,
            'model':args.model_dir,
            'decoding_method':args.decoding_method,
            'load_seconds':load,'model_bytes':sum(p.stat().st_size for p in model.iterdir()),
            'note':'Unpaced synthetic chunks: throughput, not live end-to-end latency.',
            'results':results},indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)


if __name__=='__main__':main()
