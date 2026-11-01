"""Local Ollama or explicitly configured VM relay; no global proxy/TLS changes."""
import json
from pathlib import Path
import ssl
import urllib.parse
import urllib.request
import urllib.error
import http.client
import socket
import threading


class CancelledResponse:
    """Bounded reader queue keeps Windows socket reads off the agent thread."""
    def __init__(self,connection,cancel):
        import queue
        self.connection=connection;self.cancel=cancel
        self.closed=threading.Event();self.done=threading.Event()
        self.lines=queue.Queue(maxsize=8);self.socket=None

    def __enter__(self):return self

    def __iter__(self):
        import queue
        while True:
            if self.cancel.is_set() or self.closed.is_set():raise InterruptedError('Model turn interrupted.')
            try:kind,value=self.lines.get(timeout=.03)
            except queue.Empty:continue
            if kind=='end':return
            if kind=='error':raise value
            yield value

    def close(self):
        # The pump owns HTTP file cleanup. Windows buffered socket reads can
        # block during cross-thread close, so never join it on the agent thread.
        self.closed.set()
        active=self.connection.sock or self.socket
        if active:
            try:active.shutdown(socket.SHUT_RDWR)
            except OSError:pass

    def __exit__(self,*args):self.close()

    def offer(self,kind,value=None):
        import queue
        while not self.closed.is_set() and not self.cancel.is_set():
            try:self.lines.put((kind,value),timeout=.03);return
            except queue.Full:continue
        raise InterruptedError('Model turn interrupted.')


def open_cancellable(endpoint,path,data,headers,timeout,cancel,context=None):
    if cancel.is_set():raise InterruptedError('Model turn interrupted.')
    url=urllib.parse.urlsplit(endpoint)
    cls=http.client.HTTPSConnection if url.scheme=='https' else http.client.HTTPConnection
    options={'timeout':min(timeout,8)}
    if context is not None:options['context']=context
    connection=cls(url.hostname,url.port,**options)
    wrapper=CancelledResponse(connection,cancel)
    def watch():
        while not wrapper.done.wait(.03):
            if cancel.is_set() or wrapper.closed.is_set():wrapper.close()
    def pump():
        response=None
        try:
            if cancel.is_set() or wrapper.closed.is_set():raise InterruptedError('Model turn interrupted.')
            connection.connect();wrapper.socket=connection.sock
            if cancel.is_set() or wrapper.closed.is_set():raise InterruptedError('Model turn interrupted.')
            connection.sock.settimeout(timeout)
            connection.request('POST',path,body=data,headers=headers)
            response=connection.getresponse()
            if response.status>=400:raise urllib.error.HTTPError(endpoint+path,response.status,response.reason,response.headers,None)
            for line in response:wrapper.offer('line',line)
            wrapper.offer('end')
        except Exception as error:
            if not cancel.is_set() and not wrapper.closed.is_set():
                if isinstance(error,OSError) and not isinstance(error,urllib.error.HTTPError):error=RuntimeError('The model connection did not finish. Check that the configured model service is running and ready.')
                try:wrapper.offer('error',error)
                except InterruptedError:pass
        finally:
            wrapper.done.set()
            connection.close()
            if response:response.close()
    threading.Thread(target=watch,daemon=True,name='Model cancellation').start()
    threading.Thread(target=pump,daemon=True,name='Model stream reader').start()
    return wrapper


class ModelConnection:
    def __init__(self, root):
        path = Path(root) / 'model-connection.json'
        self.remote = path.exists()
        self.endpoint = 'http://127.0.0.1:11434'
        self.headers = {}
        self.ssl_context=None
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
            self.ssl_context=context
            handlers.append(urllib.request.HTTPSHandler(context=context))
        self.opener = urllib.request.build_opener(*handlers)

    def open(self, path, data=None, timeout=240, cancel=None):
        if path not in {'/api/version', '/api/tags', '/api/chat'}:
            raise ValueError('Unsupported model API path')
        headers = dict(self.headers)
        if data is not None:
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.endpoint + path, data=data, headers=headers)
        try:
            if cancel is not None and path=='/api/chat':
                return open_cancellable(self.endpoint,path,data,headers,timeout,cancel,self.ssl_context)
            return self.opener.open(request, timeout=timeout)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, TimeoutError) as error:
            if self.remote:
                raise RuntimeError('The connection to the host model did not finish. Check that the host model server and encrypted VM relay are running and ready, then try again. The first start after a reboot can take longer.') from error
            raise RuntimeError('The local model connection did not finish. Check that the model server is running and ready, then try again.') from error
