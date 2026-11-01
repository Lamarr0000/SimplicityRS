"""Local acceptance checks; prints no authentication material."""
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.request

root=Path(__file__).resolve().parent
config=json.loads((root/'relay-private.json').read_text())
url='https://192.168.182.1:11436'
context=ssl.create_default_context(cafile=str(root/'server-cert.pem'))
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=context))
headers={'X-ThemHands-Model-Key':config['token'],'Content-Type':'application/json'}
def denied(path, expected, data=None, authenticated=True):
    try:
        opener.open(urllib.request.Request(url+path,data=data,headers=headers if authenticated else {}),timeout=5)
    except urllib.error.HTTPError as e:
        assert e.code==expected,(path,e.code)
        print(f'{path}: rejected as expected ({expected})')
    else:
        raise AssertionError('Unexpectedly allowed request')
denied('/api/version',403,authenticated=False)
denied('/api/pull',404,data=b'{}')
denied('/api/chat',400,data=json.dumps({'model':'other-model'}).encode())
with opener.open(urllib.request.Request(url+'/api/version',headers=headers),timeout=8) as r:
    print('Authenticated TLS version check:',json.load(r)['version'])
with opener.open(urllib.request.Request(url+'/api/tags',headers=headers),timeout=8) as r:
    names=[m['name'] for m in json.load(r)['models']]
    assert names==['gpt-oss:20b'],names
    print('Only gpt-oss:20b is exposed')
try:
    untrusted=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    untrusted.open(urllib.request.Request(url+'/api/version',headers=headers),timeout=5)
except urllib.error.URLError as e:
    assert isinstance(e.reason,ssl.SSLCertVerificationError),type(e.reason)
    print('Untrusted certificate rejected without the dedicated CA')
else:
    raise AssertionError('Expected certificate verification failure')
