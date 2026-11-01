"""Exercise authenticated shutdown and exact owned-process cleanup."""
import json
import threading
import unittest
import urllib.request
import urllib.error
import subprocess
import sys
import psutil
from unittest.mock import patch, Mock
from http.server import ThreadingHTTPServer
import app
import window_launcher


class WindowLifecycle(unittest.TestCase):
    def test_job_cleanup_stops_owned_descendants_and_preserves_sibling(self):
        code = "import subprocess,sys,time;sys.stdin.readline();p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);print(p.pid,flush=True);time.sleep(60)"
        sibling = subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW)
        owned = subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        guard = None
        try:
            guard = window_launcher._guard_process(owned)
            owned.stdin.write('\n');owned.stdin.flush()
            descendant = psutil.Process(int(owned.stdout.readline()))
            guard();guard=None
            owned.wait(timeout=5)
            descendant.wait(timeout=5)
            self.assertIsNone(sibling.poll())
        finally:
            if guard:guard()
            if owned.poll() is None:owned.terminate();owned.wait(timeout=5)
            sibling.terminate();sibling.wait(timeout=5)
            owned.stdin.close();owned.stdout.close()

    def test_shutdown_requires_token_and_origin_and_stops_workers(self):
        with patch('app.VOICE') as voice, patch('app.SPEECH') as speech, patch('app.STATE') as state:
            server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            url = 'http://127.0.0.1:' + str(server.server_port)
            def send(token, origin=None):
                headers = {'X-ThemHands-Token': token}
                if origin: headers['Origin'] = origin
                return urllib.request.urlopen(urllib.request.Request(url+'/shutdown',data=b'{}',headers=headers))
            try:
                for token, origin in [('wrong',None),(app.TOKEN,'https://example.com')]:
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        send(token,origin)
                    self.assertEqual(error.exception.code,403)
                    error.exception.close()
                voice.stop.assert_not_called()
                with send(app.TOKEN) as response:
                    self.assertTrue(json.load(response)['ok'])
                thread.join(3)
                self.assertFalse(thread.is_alive())
                voice.stop.assert_called_once()
                speech.stop.assert_called_once()
                state.stop.assert_called_once()
            finally:
                if thread.is_alive(): server.shutdown()
                server.server_close()

    def test_existing_service_is_not_taken_over(self):
        with patch('pathlib.Path.is_file',return_value=True), patch('window_launcher.request',return_value={'app':'ThemHands'}), patch('window_launcher.subprocess.Popen') as start:
            with self.assertRaisesRegex(RuntimeError,'already running'):
                window_launcher.launch()
            start.assert_not_called()

    def test_window_close_requests_shutdown_and_closes_owned_jobs(self):
        server, shell = Mock(), Mock()
        server.poll.side_effect=[None,None]
        guard_server, guard_shell = Mock(), Mock()
        with patch('pathlib.Path.is_file',return_value=True), patch('pathlib.Path.mkdir'), patch('pathlib.Path.open'), patch('pathlib.Path.read_text',return_value='http://127.0.0.1:8769/#token'), patch('window_launcher.request',side_effect=[OSError(),{'app':'ThemHands'},{'ok':True}]) as request, patch('window_launcher.subprocess.Popen',side_effect=[server,shell]), patch('window_launcher._guard_process',side_effect=[guard_server,guard_shell]):
            window_launcher.launch()
            self.assertEqual(request.call_args.args,('/shutdown','token',{}))
            server.wait.assert_called_once_with(timeout=5)
            shell.wait.assert_called_once_with()
            guard_server.assert_called_once_with()
            guard_shell.assert_called_once_with()
            server.terminate.assert_not_called()


if __name__ == '__main__': unittest.main()
