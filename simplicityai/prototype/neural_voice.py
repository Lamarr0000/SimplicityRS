"""Local Whisper capture with the same opt-in/cancellation controls."""
from pathlib import Path
from voice import VoiceInput

ROOT=Path(__file__).resolve().parent


class NeuralVoiceInput(VoiceInput):
    capture_timeout=65
    modes={'Listen','Probe','Level'}

    def __init__(self):
        super().__init__()
        self.state={'state':'idle','message':'Click Talk to start local voice input. Typing is always available.'}

    def command(self, mode):
        assets=ROOT/'whisper'
        if not assets.is_dir(): assets=ROOT.parent/'SpeechConversation'
        runtime=assets/'python'/'cpython-3.12.16-windows-x86_64-none'/'python.exe'
        if not runtime.is_file() or not (assets/'models'/'small.en'/'model.bin').is_file():
            raise ValueError('Local Whisper speech files are missing')
        return [str(runtime),str(ROOT/'whisper_worker.py'),str(assets),mode]
