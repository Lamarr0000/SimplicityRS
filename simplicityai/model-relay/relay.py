"""VM-only TLS relay. The host model never executes guest tools."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import ssl
import threading

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'relay-private.json').read_text(encoding='utf-8'))
SLOT = threading.BoundedSemaphore(1)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def log_message(self, *args):
        pass  # Never log prompts, tokens, or responses.

    def reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        return (self.client_address[0] in {CONFIG['guest_ip'], CONFIG['host_ip']}
                and secrets.compare_digest(self.headers.get('X-ThemHands-Model-Key', ''), CONFIG['token']))

    def do_GET(self):
        if not self.authorized():
            return self.reply(403, {'error': 'Unauthorized VM model connection'})
        if self.path not in {'/api/version', '/api/tags'}:
            return self.reply(404, {'error': 'Unsupported path'})
        connection = http.client.HTTPConnection('127.0.0.1', 11434, timeout=8)
        try:
            connection.request('GET', self.path)
            response = connection.getresponse()
            payload = json.loads(response.read())
            if self.path == '/api/tags':
                payload['models'] = [m for m in payload.get('models', []) if m.get('name') == 'gpt-oss:20b']
            self.reply(response.status, payload)
        except (OSError, ValueError):
            self.reply(502, {'error': 'Host Ollama is unavailable'})
        finally:
            connection.close()

    def do_POST(self):
        if not self.authorized():
            return self.reply(403, {'error': 'Unauthorized VM model connection'})
        if self.path != '/api/chat':
            return self.reply(404, {'error': 'Unsupported path'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 262144:
                raise ValueError('Invalid request size')
            payload = json.loads(self.rfile.read(length))
            if payload.get('model') != 'gpt-oss:20b':
                raise ValueError('Only gpt-oss:20b is offered')
            options = payload.setdefault('options', {})
            options['num_ctx'] = min(int(options.get('num_ctx', 8192)), 8192)
            options['num_predict'] = min(max(int(options.get('num_predict', 900)), 1), 1000)
            payload['keep_alive'] = '15m'
            body = json.dumps(payload).encode()
        except (ValueError, TypeError, AttributeError):
            return self.reply(400, {'error': 'Invalid model request'})
        if not SLOT.acquire(blocking=False):
            return self.reply(429, {'error': 'The VM model relay is busy; retry shortly'})
        connection = http.client.HTTPConnection('127.0.0.1', 11434, timeout=240)
        try:
            connection.request('POST', '/api/chat', body, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/x-ndjson'))
            self.end_headers()
            if payload.get('stream', True):
                for line in response:
                    self.wfile.write(line)
                    self.wfile.flush()
            else:
                self.wfile.write(response.read())
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            connection.close()
            SLOT.release()


server = ThreadingHTTPServer((CONFIG['host_ip'], 11436), Handler)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.load_cert_chain(ROOT / 'server-cert.pem', ROOT / 'server-key.pem')
server.socket = context.wrap_socket(server.socket, server_side=True)
print('ThemHands VM relay ready on VMnet8:11436 (TLS, IP allowlist and token required)', flush=True)
server.serve_forever()
