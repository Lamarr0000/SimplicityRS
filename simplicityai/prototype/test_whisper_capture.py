import contextlib
import io
import itertools
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock,patch
import whisper_worker


class CaptureTests(unittest.TestCase):
    def test_level_test_uses_native_rate_and_never_loads_recognizer(self):
        class Block:
            value=.01
            def copy(self):return self
            def __mul__(self,other):return types.SimpleNamespace(value=self.value**2)
            def __getitem__(self,key):return self
            def __len__(self):return 4800
        settings={}
        class Stream:
            def __init__(self,**kwargs):settings.update(kwargs);self.callback=kwargs['callback']
            def __enter__(self):
                for _ in range(10):self.callback(Block(),4800,None,None)
                return self
            def __exit__(self,*args):pass
        numpy=types.SimpleNamespace(sqrt=math.sqrt,mean=lambda block:block.value)
        sound=types.SimpleNamespace(query_devices=lambda **kwargs:{'name':'Synthetic microphone','max_input_channels':1,'default_samplerate':48000},InputStream=Stream)
        model=Mock(side_effect=AssertionError('Level test must not load a model'))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'models'/'small.en').mkdir(parents=True);(root/'models'/'small.en'/'model.bin').write_bytes(b'fixture')
            clock=itertools.count();output=io.StringIO()
            with patch.dict(sys.modules,{'numpy':numpy,'sounddevice':sound,'faster_whisper':types.SimpleNamespace(WhisperModel=model)}),patch.object(sys,'argv',['worker',directory,'Level']),patch.object(sys,'path',list(sys.path)),patch.object(whisper_worker.time,'monotonic',lambda:next(clock)),contextlib.redirect_stdout(output):
                whisper_worker.main()
            result=json.loads(output.getvalue().splitlines()[-1])
            self.assertEqual(settings['samplerate'],48000)
            self.assertEqual(result['state'],'ready')
            self.assertGreater(result['peak_rms'],0)
            model.assert_not_called()


if __name__=='__main__':unittest.main()
