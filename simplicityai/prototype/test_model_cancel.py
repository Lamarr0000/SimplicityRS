import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from model_connection import open_cancellable


class RequestCancellation(unittest.TestCase):
    def test_cancellation_wakes_blocked_stream_for_both_http_versions(self):
        for protocol in ['HTTP/1.0','HTTP/1.1']:
            with self.subTest(protocol=protocol):self.run_blocked_test(protocol)

    def run_blocked_test(self,protocol):
        received=threading.Event();release=threading.Event()
        class Handler(BaseHTTPRequestHandler):
            protocol_version=protocol
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.end_headers()
                self.wfile.write(b'{"message":{"content":"first"}}\n');self.wfile.flush();received.set();release.wait(5)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.daemon_threads=True
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        cancel=threading.Event();outcome=[]
        def read():
            try:
                with open_cancellable('http://127.0.0.1:'+str(server.server_port),'/api/chat',b'{}',{'Content-Type':'application/json'},20,cancel) as response:
                    for line in response:json.loads(line)
            except InterruptedError:outcome.append('cancelled')
        worker=threading.Thread(target=read,daemon=True);worker.start()
        try:
            self.assertTrue(received.wait(2));start=time.monotonic();cancel.set();worker.join(1)
            self.assertFalse(worker.is_alive(),'Reader remained blocked after interruption')
            self.assertEqual(outcome,['cancelled']);self.assertLess(time.monotonic()-start,1)
        finally:release.set();server.shutdown();server.server_close();worker.join(2)

    def test_pre_cancelled_request_does_not_connect(self):
        cancel=threading.Event();cancel.set()
        with self.assertRaises(InterruptedError):open_cancellable('http://127.0.0.1:1','/api/chat',b'{}',{},10,cancel)

    def test_complete_stream_is_delivered_without_cancellation(self):
        body=b'{"done":true}\n'
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with open_cancellable('http://127.0.0.1:'+str(server.server_port),'/api/chat',b'{}',{},5,threading.Event()) as response:self.assertEqual(list(response),[body])
        finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
