import base64
import io
import json
import unittest
from unittest.mock import Mock, patch
from kokoro_speech import KokoroSpeech


class KokoroTests(unittest.TestCase):
    def test_text_bound_before_launch(self):
        for text in [None, '', 'x'*2001]:
            with self.assertRaises(ValueError):
                KokoroSpeech().synthesize(text)

    @patch('kokoro_speech.Path.is_file', return_value=True)
    @patch('kokoro_speech.Path.is_dir', return_value=True)
    @patch('kokoro_speech._guard_process')
    @patch('kokoro_speech.subprocess.Popen')
    def test_reuses_owned_worker_and_passes_text_as_data(self, popen, guard, directory, file):
        wav=b'RIFF\x00\x00\x00\x00WAVEaudio'
        line=json.dumps({'audio':base64.b64encode(wav).decode()}).encode()+b'\n'
        process=Mock(stdin=io.BytesIO(),stdout=io.BytesIO(line+line))
        process.poll.return_value=None
        popen.return_value=process
        speaker=KokoroSpeech()
        self.assertEqual(speaker.synthesize('hello'),wav)
        self.assertEqual(speaker.synthesize('do not execute $(anything)'),wav)
        self.assertEqual(popen.call_count,1)
        self.assertNotIn('do not execute',str(popen.call_args))
        speaker.stop()
        process.terminate.assert_called_once()
        guard.return_value.assert_called_once()

    @patch('kokoro_speech.Path.is_file', return_value=True)
    @patch('kokoro_speech.Path.is_dir', return_value=True)
    @patch('kokoro_speech._guard_process')
    @patch('kokoro_speech.subprocess.Popen')
    def test_invalid_output_stops_worker(self, popen, guard, directory, file):
        process=Mock(stdin=io.BytesIO(),stdout=io.BytesIO(b'not audio\n'))
        process.poll.return_value=None
        popen.return_value=process
        speaker=KokoroSpeech()
        with self.assertRaises(ValueError):
            speaker.synthesize('hello')
        self.assertIsNone(speaker.process)
        self.assertFalse(speaker.busy)


if __name__=='__main__':
    unittest.main()
