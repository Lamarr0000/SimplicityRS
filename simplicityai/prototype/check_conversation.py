"""Opt-in guest speech check. No microphone activation or network diagnostics."""
import json
from pathlib import Path
import time
from kokoro_speech import KokoroSpeech
from neural_voice import NeuralVoiceInput


def main():
    root=Path(__file__).resolve().parent
    logs=root/'logs';logs.mkdir(exist_ok=True)
    lines=['Local speech diagnostic; no microphone recording or network changes.']
    speaker=KokoroSpeech()
    try:
        start=time.monotonic()
        audio=speaker.synthesize('Hello. SimplicityAI voice playback is ready.')
        path=logs/'voice-check.wav';path.write_bytes(audio)
        lines.append(f'Kokoro audio generation passed in {time.monotonic()-start:.1f} seconds.')
        lines.append('To test your speakers independently of the browser, open: '+str(path))
    except Exception as error:
        lines.append('Kokoro failed: '+str(error))
        lines.append('Technical detail: '+speaker.last_error)
    finally:speaker.stop()
    voice=NeuralVoiceInput();voice.start('Probe')
    for _ in range(150):
        state=voice.snapshot()
        if state['state']!='starting':break
        time.sleep(.1)
    else:
        voice.stop();state=voice.snapshot()
    lines.append('Whisper/device probe: '+json.dumps(state))
    report='\n\n'.join(lines)
    (logs/'conversation-check.txt').write_text(report,encoding='utf-8')
    print(report)


if __name__=='__main__':main()
