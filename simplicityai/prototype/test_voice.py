import io
import unittest
import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from unittest.mock import Mock, patch
from voice import VoiceInput
import app


class VoiceTests(unittest.TestCase):
    def setUp(self):
        guard = patch('voice._guard_process', return_value=lambda: None)
        guard.start()
        self.addCleanup(guard.stop)

    @patch('voice.subprocess.Popen')
    def test_probe_uses_fixed_script_without_audio_or_network_command(self, popen):
        process = Mock(stdout=io.StringIO('{"state":"ready","message":"Engine found"}\n'))
        process.poll.return_value = 0
        popen.return_value = process
        voice = VoiceInput()
        voice._run('Probe', 0)
        command = popen.call_args.args[0]
        self.assertEqual(command[-2:], ['-Mode', 'Probe'])
        self.assertTrue(command[-3].endswith('Voice-Input.ps1'))
        self.assertEqual(voice.snapshot()['state'], 'ready')

    def test_only_named_modes_and_one_capture(self):
        voice = VoiceInput()
        with self.assertRaises(ValueError):
            voice.start('arbitrary command')
        voice.state = {'state': 'listening'}
        with self.assertRaises(ValueError):
            voice.start()

    @patch('voice.subprocess.Popen')
    def test_cancelled_capture_cannot_start_or_publish_words(self, popen):
        voice = VoiceInput()
        voice.stop()
        voice._run('Listen', 0)
        popen.assert_not_called()
        self.assertEqual(voice.snapshot()['state'], 'cancelled')
        self.assertNotIn('text', voice.snapshot())

    @patch('voice.subprocess.Popen')
    def test_transcription_remains_text_only(self, popen):
        process = Mock(stdout=io.StringIO('{"state":"listening"}\n{"state":"transcribed","text":"Repair everything"}\n'))
        process.poll.return_value = 0
        popen.return_value = process
        voice = VoiceInput()
        voice._run('Listen', 0)
        self.assertEqual(voice.snapshot()['text'], 'Repair everything')
        self.assertFalse(hasattr(voice, 'execute'))


class VoiceEndpointTests(unittest.TestCase):
    def setUp(self):
        self.voice = Mock()
        self.voice.snapshot.return_value = {'state': 'listening'}
        self.state = Mock(busy=False)
        for name, value in [('VOICE', self.voice), ('STATE', self.state)]:
            patcher = patch.object(app, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def test_voice_requires_session_token(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.opener.open(self.url + '/voice/state')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        self.voice.snapshot.assert_not_called()

    def test_task_cannot_start_during_capture(self):
        request = urllib.request.Request(self.url + '/start', data=json.dumps({'prompt': 'test'}).encode(),
                    headers={'X-ThemHands-Token': app.TOKEN, 'Content-Type': 'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.opener.open(request)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        self.state.start.assert_not_called()


if __name__ == '__main__':
    unittest.main()
