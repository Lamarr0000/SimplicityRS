"""Headless synthetic checks. Never opens a microphone or plays audio."""
import asyncio
import base64
import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
import wave

from protocol import Segments
from voice_worker import Gate


class ProtocolTests(unittest.TestCase):
    def test_tool_activity_and_confirmation_use_real_adapter(self):
        import server
        events=[]
        agent=server.Agent(lambda kind,**data:events.append((kind,data)),'gpt-oss:20b')
        agent.state.chat.begin('Use this VM.')
        result=agent.state.execute({'function':{'name':'confirm_running_windows','arguments':{}}})
        self.assertTrue(result['confirmed'])
        self.assertEqual(events[0][0],'activity')
        self.assertEqual(events[0][1]['activity_kind'],'tool_request')

    def test_segments(self):
        text='First useful sentence. '+('A bounded piece of conversation. '*12)
        parts=Segments();out=[]
        for end in range(len(text)+1):out+=parts.feed(text[:end])
        out+=parts.feed(text,final=True)
        self.assertEqual(' '.join(' '.join(out).split()),' '.join(text.split()))
        self.assertLessEqual(len(out[0]),80)
        with self.assertRaises(ValueError):parts.feed('changed')

    def test_vad_bounds_and_noise(self):
        gate=Gate()
        for _ in range(30):self.assertIsNone(gate.feed(b'x',.1)[0])
        for _ in range(2):self.assertIsNone(gate.feed(b'x',.9)[0])
        self.assertEqual(gate.feed(b'x',.9)[0],'start')
        for _ in range(19):self.assertNotEqual(gate.feed(b'x',.1)[0],'end')
        self.assertEqual(gate.feed(b'x',.1)[0],'end')

    def test_agent_scope_and_tool_gate(self):
        import server
        state=server.State();state.mode='chat'
        for name,args in [('shell',{}),('get_network_snapshot',{}),
                          ('get_health_snapshot',{'command':'whoami'}),
                          ('calculate_in_calculator',{'expression':'__import__("os")'})]:
            with self.assertRaises((ValueError,RuntimeError)):
                state.execute({'function':{'name':name,'arguments':args}})

    def test_agent_routes_tool_without_speaking_json(self):
        import server
        events=[];spoken=[];calls=[]
        agent=server.Agent(lambda kind,**data:events.append((kind,data)),'gpt-oss:20b')
        agent.state.execute=lambda call:calls.append(call) or {'ok':True,'result':'synthetic evidence'}
        class Response:
            def __init__(self,text=None,call=None):self.text=text;self.call=call
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __iter__(self):
                if self.call:yield json.dumps({'message':{'tool_calls':[self.call]}}).encode()
                for char in self.text or '':yield json.dumps({'message':{'content':char}}).encode()
                yield b'{"done":true,"done_reason":"stop"}'
        replies=iter([Response(call={'function':{'name':'get_health_snapshot','arguments':{}}}),
                      Response('The synthetic check finished. Its cause remains unknown.')])
        with patch.object(agent.connection,'open',side_effect=lambda *a,**kw:next(replies)):
            agent.run('A synthetic test only.',spoken.append)
        self.assertEqual(len(calls),1)
        self.assertNotIn('arguments',' '.join(spoken))
        self.assertIn('cause remains unknown',' '.join(spoken))


class SessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_stale_events_and_cancellation(self):
        import server
        class Socket:
            def __init__(self):self.events=[]
            async def send_json(self,value):self.events.append(value)
        ws=Socket();session=server.Session(ws,'gpt-oss:20b',io.StringIO())
        session.turn=2;session.agent.running_turn=1
        await asyncio.to_thread(session.thread_emit,'text.delta',text='stale')
        self.assertEqual(ws.events,[])
        await session.control({'type':'cancel'})
        self.assertTrue(session.agent.state.cancel.is_set())
        self.assertEqual(session.turn,3)
        await session.control({'type':'reset'})
        self.assertIsNone(session.agent.state.chat.target)

    async def test_audio_queue_is_bounded_and_reset_discards_frames(self):
        import server
        class Socket:
            async def send_json(self,value):pass
        session=server.Session(Socket(),'gpt-oss:20b',io.StringIO())
        for i in range(64):session.frames.put_nowait((0,b'x'))
        with self.assertRaises(asyncio.QueueFull):session.frames.put_nowait((0,b'x'))
        await session.set_listening(False)
        self.assertEqual(session.frames.qsize(),1)
        self.assertEqual(await session.frames.get(),(1,None))


def recognition():
    import server
    import array
    fixture=Path('C:/SimplicityAI-Lab/ThemHands/logs/asr-expanded-fixtures.json')
    samples=json.loads(fixture.read_text(encoding='utf-8-sig'))
    worker=server.VoiceWorker();worker.start();results=[]
    try:
        for sample in samples:
            worker.request(None)
            with wave.open(io.BytesIO(base64.b64decode(sample['audio'])),'rb') as wav:
                rate=wav.getframerate();source=array.array('h',wav.readframes(wav.getnframes()))
            # Deterministic synthetic fixture resampling; live client uses Web Audio.
            pcm=array.array('h',(source[min(int(i*rate/16000),len(source)-1)] for i in range(int(len(source)*16000/rate)))).tobytes()
            pcm=b'\0'*16000+pcm+b'\0'*32000
            events=[];started=time.monotonic()
            for i in range(0,len(pcm),1024):
                events.extend(worker.request(pcm[i:i+1024].ljust(1024,b'\0')))
            results.append({'expected':sample['text'],'events':events,'processing_seconds':time.monotonic()-started})
    finally:worker.close()
    target=server.ASSETS/'logs/recognition-check.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))


async def benchmark():
    import server
    from aiohttp import ClientSession, web
    app=server.create_app();runner=web.AppRunner(app,access_log=None);await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1];results=[]
    try:
        async with ClientSession() as client:
            async with client.ws_connect(f'http://127.0.0.1:{port}/session') as ws:
                await ws.send_json({'token':server.TOKEN})
                while True:
                    value=await ws.receive_json(timeout=180)
                    if value['type']=='error':raise RuntimeError(value['text'])
                    if value['type']=='ready':break
                # Text isolates model+speech latency; no OS tools are permitted in this check.
                session=app['session']
                def forbid(call):raise RuntimeError('Windows tools disabled in synthetic benchmark')
                session.agent.state.execute=forbid
                for prompt in ['Explain the difference between RAM and storage in two short sentences.',
                               'What should I tell you first if my computer will not start?']:
                    start=time.monotonic();first_text=None;first_audio=None;done=None;timings=[];turn=None
                    await ws.send_json({'type':'chat','text':prompt})
                    while first_audio is None or done is None:
                        value=await ws.receive_json(timeout=180);elapsed=time.monotonic()-start
                        if value['type']=='error':raise RuntimeError(value['text'])
                        if value['type']=='turn.start':turn=value['turn']
                        if turn is None or value.get('turn')!=turn:continue
                        if value['type']=='text.delta' and first_text is None:first_text=elapsed
                        if value['type']=='audio' and first_audio is None:first_audio=elapsed
                        if value['type']=='model.timing':timings.append(value)
                        if value['type']=='turn.done':done=elapsed
                    results.append({'prompt':prompt,'first_useful_text_seconds':first_text,
                                    'first_audio_available_seconds':first_audio,'text_complete_seconds':done,'model':timings})
                    # Drain prior reply synthesis before the next benchmark.
                    await asyncio.sleep(3)
                await ws.send_json({'type':'close'})
    finally:await runner.cleanup()
    target=server.ASSETS/'logs/streaming-benchmark.json'
    target.write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))


async def voice_benchmark(model='gpt-oss:20b',prompt='Explain RAM in one short sentence.',label=''):
    """Real-time synthetic PCM input through the complete server. No mic/playback."""
    import array
    import server
    from aiohttp import ClientSession, web
    app=server.create_app(model);runner=web.AppRunner(app,access_log=None);await runner.setup()
    site=web.TCPSite(runner,'127.0.0.1',0);await site.start()
    port=site._server.sockets[0].getsockname()[1];result={}
    try:
        async with ClientSession() as client:
            async with client.ws_connect(f'http://127.0.0.1:{port}/session') as ws:
                await ws.send_json({'token':server.TOKEN})
                while True:
                    value=await ws.receive_json(timeout=180)
                    if value['type']=='error':raise RuntimeError(value['text'])
                    if value['type']=='ready':break
                session=app['session']
                session.agent.state.execute=lambda call:(_ for _ in ()).throw(RuntimeError('Windows tools disabled in benchmark'))
                audio=await asyncio.to_thread(session.speaker.synthesize,prompt)
                with wave.open(io.BytesIO(audio),'rb') as wav:
                    rate=wav.getframerate();source=array.array('h',wav.readframes(wav.getnframes()))
                pcm=array.array('h',(source[min(int(i*rate/16000),len(source)-1)] for i in range(int(len(source)*16000/rate))))
                last=max(i for i,v in enumerate(pcm) if abs(v)>160)
                pcm=b'\0'*16000+pcm.tobytes()+b'\0'*64000
                await ws.send_json({'type':'listen','enabled':True})
                started=time.monotonic();end=started+.5+(last+1)/16000
                async def feed():
                    for offset in range(0,len(pcm),1024):
                        await asyncio.sleep(max(0,started+offset/32000-time.monotonic()))
                        await ws.send_bytes(pcm[offset:offset+1024].ljust(1024,b'\0'))
                feeder=asyncio.create_task(feed());turn=None;first_audio=None;useful_audio=None;spoken_segment='';done=False;events=[]
                while useful_audio is None or not done:
                    value=await ws.receive_json(timeout=180);now=time.monotonic()
                    if value['type']=='error':raise RuntimeError(value['text'])
                    if value['type']=='turn.start':turn=value['turn']
                    if value['type']=='speech.timing' and value.get('turn')==turn:spoken_segment=value.get('text','')
                    if value['type']=='audio' and value.get('turn')==turn and turn is not None:
                        if first_audio is None:first_audio=now-end
                        if useful_audio is None and spoken_segment.strip().lower().strip('.! ') not in {'sure','sure thing','okay','ok','yes','got it','of course'}:
                            useful_audio=now-end
                    if value['type']=='turn.done' and value.get('turn')==turn:done=True
                    if value['type']!='audio':events.append({'after_end_seconds':now-end,**value})
                await feeder
                await ws.send_json({'type':'listen','enabled':False})
                result={'model':model,'synthetic_input':prompt,'first_audio_available_after_speech_end_seconds':first_audio,
                        'first_non_acknowledgment_audio_after_speech_end_seconds':useful_audio,
                        'semantic_correctness':'Requires manual comparison of transcript and reply with intended input',
                        'physical_playback_tested':False,'events':events}
                await ws.send_json({'type':'close'})
    finally:await runner.cleanup()
    target=server.ASSETS/'logs'/('voice-streaming-'+model.replace(':','-')+label+'.json');target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    if '--recognition' in sys.argv:recognition()
    elif '--voice-benchmark' in sys.argv:asyncio.run(voice_benchmark(sys.argv[sys.argv.index('--model')+1] if '--model' in sys.argv else 'gpt-oss:20b'))
    elif '--benchmark' in sys.argv:asyncio.run(benchmark())
    else:unittest.main()
