import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from stream_asr import worker_configuration
from zipformer_worker import ShortWordFallback, verify_short


class FastRecognitionTests(unittest.TestCase):
    def test_ambiguous_short_words_are_verified_not_silently_corrected(self):
        for text in ('COUNSEL','CANCE','uncertain'):
            self.assertTrue(verify_short(text))
        for text in ('','YES','NO','STOP','CANCEL','STOP TALKING','I DO NOT HAVE THE KEY'):
            self.assertFalse(verify_short(text))

    def test_backend_requires_explicit_fixed_marker_and_keeps_whisper_default(self):
        with tempfile.TemporaryDirectory() as directory:
            app=Path(directory)/'app';app.mkdir()
            with patch('stream_asr.ROOT',app):
                runtime,args=worker_configuration()
                self.assertTrue(args[0].endswith('stream_asr_worker.py'))
                assets=Path(directory)/'SpeechStreaming';assets.mkdir()
                marker=assets/'backend.json'
                marker.write_text(json.dumps({'schema':1,'backend':'zipformer20230626'}))
                runtime,args=worker_configuration()
                self.assertTrue(args[0].endswith('zipformer_worker.py'))
                self.assertEqual(args[1],str(assets))
                self.assertEqual(args[2],str(Path(directory)/'SpeechConversation'))
                marker.write_text('{"schema":1,"backend":"arbitrary-command"}')
                with self.assertRaises(ValueError):worker_configuration()

    @patch('zipformer_worker.subprocess.Popen')
    def test_fallback_is_lazy_reused_and_receives_audio_as_data(self,popen):
        fallback=ShortWordFallback(Path('fixed-assets'))
        popen.assert_not_called()
        process=Mock(stdin=io.BytesIO(),stdout=io.BytesIO(
            b'{"ready":true}\n{"text":"Cancel."}\n{"text":"Again."}\n'))
        process.poll.return_value=None;popen.return_value=process
        self.assertEqual(fallback.transcribe(b'binary audio'),'Cancel.')
        self.assertEqual(fallback.transcribe(b'new audio'),'Again.')
        popen.assert_called_once()
        self.assertNotIn('binary audio',str(popen.call_args))
        self.assertEqual(len(process.stdin.getvalue().splitlines()),2)
        fallback.close();process.terminate.assert_called_once();process.wait.assert_called_once()


if __name__=='__main__':unittest.main()
