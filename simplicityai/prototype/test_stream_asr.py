import base64
import io
import json
import unittest
import wave
from unittest.mock import Mock,patch
from stream_asr import StreamASR,validate_audio


def audio(seconds=1,channels=1,width=2):
    data=io.BytesIO()
    with wave.open(data,'wb') as wav:
        wav.setnchannels(channels);wav.setsampwidth(width);wav.setframerate(16000);wav.writeframes(b'\0'*int(seconds*16000)*width*channels)
    return data.getvalue()


class StreamingRecognition(unittest.TestCase):
    def test_valid_native_pcm_and_invalid_bounds(self):
        validate_audio(audio())
        for value in [b'not a wav',audio(27),audio(.05),audio(channels=2),audio(width=1),audio()[:-100]]:
            with self.assertRaises(ValueError):validate_audio(value)

    @patch('stream_asr.Path.is_file',return_value=True)
    @patch('stream_asr.Path.is_dir',return_value=True)
    @patch('stream_asr._guard_process')
    @patch('stream_asr.subprocess.Popen')
    def test_warm_worker_is_retained_and_audio_remains_data(self,popen,guard,directory,file):
        process=Mock(stdin=io.BytesIO(),stdout=io.BytesIO(b'{"ready":true}\n{"text":"hello"}\n{"text":"again"}\n'))
        process.poll.return_value=None;popen.return_value=process
        recognizer=StreamASR()
        self.assertTrue(recognizer.run()['ready']);recognizer.cancel();process.terminate.assert_not_called()
        self.assertEqual(recognizer.run(audio())['text'],'hello')
        self.assertEqual(recognizer.run(audio())['text'],'again')
        self.assertEqual(popen.call_count,1)
        payload=json.loads(process.stdin.getvalue().splitlines()[0]);self.assertEqual(base64.b64decode(payload['audio']),audio())
        recognizer.stop();process.terminate.assert_called_once();guard.return_value.assert_called_once()

    @patch('stream_asr.subprocess.Popen')
    def test_malformed_audio_cannot_launch_worker(self,popen):
        with self.assertRaises(ValueError):StreamASR().run(b'arbitrary data')
        popen.assert_not_called()


if __name__=='__main__':unittest.main()
