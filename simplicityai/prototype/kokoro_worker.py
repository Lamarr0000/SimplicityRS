"""Fixed-voice CPU synthesis worker. Input JSON, output WAV; no network calls."""
import contextlib
import base64
import io
import json
from pathlib import Path
import sys
import wave


def main():
    assets = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(assets / 'deps'))
    with contextlib.redirect_stdout(sys.stderr):
        import numpy as np
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        ort.disable_telemetry_events()
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.log_severity_level = 3
        session = ort.InferenceSession(str(assets / 'models' / 'kokoro-v1.0.onnx'),
                    sess_options=options, providers=['CPUExecutionProvider'])
        kokoro = Kokoro.from_session(session, str(assets / 'models' / 'voices-v1.0.bin'))
    for line in sys.stdin.buffer:
        text = json.loads(line).get('text')
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 2000:
            raise ValueError('Expected text of at most 2000 characters')
        with contextlib.redirect_stdout(sys.stderr):
            samples, rate = kokoro.create(text.strip(), voice='af_heart', speed=1.0, lang='en-us')
            pcm = (np.clip(samples, -1, 1) * 32767).astype('<i2').tobytes()
        audio = io.BytesIO()
        with wave.open(audio, 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(rate)
            output.writeframes(pcm)
        sys.stdout.buffer.write(json.dumps({'audio': base64.b64encode(audio.getvalue()).decode('ascii')}).encode()+b'\n')
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
