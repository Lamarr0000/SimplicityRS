"""Local Ollama or explicitly configured VM relay; no global proxy/TLS changes."""
import json
from pathlib import Path
import ssl
import urllib.parse
import urllib.request
import urllib.error


class ModelConnection:
    def __init__(self, root):
        path = Path(root) / 'model-connection.json'
        self.remote = path.exists()
        self.endpoint = 'http://127.0.0.1:11434'
        self.headers = {}
        handlers = [urllib.request.ProxyHandler({})]
        if self.remote:
            config = json.loads(path.read_text(encoding='utf-8-sig'))
            self.endpoint = config['endpoint'].rstrip('/')
            url = urllib.parse.urlsplit(self.endpoint)
            if (url.scheme != 'https' or url.hostname != '192.168.182.1'
                    or url.port != 11436 or url.path or url.username or url.password
                    or url.query or url.fragment):
                raise ValueError('Unexpected VM model relay address')
            token = config['token']
            if not isinstance(token, str) or len(token) < 32:
                raise ValueError('Missing model relay token')
            self.headers['X-ThemHands-Model-Key'] = token
            context = ssl.create_default_context(cafile=str(Path(root) / 'model-relay-ca.pem'))
            handlers.append(urllib.request.HTTPSHandler(context=context))
        self.opener = urllib.request.build_opener(*handlers)

    def open(self, path, data=None, timeout=240):
        if path not in {'/api/version', '/api/tags', '/api/chat'}:
            raise ValueError('Unsupported model API path')
        headers = dict(self.headers)
        if data is not None:
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.endpoint + path, data=data, headers=headers)
        try:
            return self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError) as error:
            if self.remote:
                raise RuntimeError('The connection to the host model did not finish. Check that the host model server and encrypted VM relay are running and ready, then try again. The first start after a reboot can take longer.') from error
            raise RuntimeError('The local model connection did not finish. Check that the model server is running and ready, then try again.') from error
