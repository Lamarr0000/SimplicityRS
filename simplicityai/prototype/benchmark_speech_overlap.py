"""Synthetic text-to-ready-audio comparison. No microphone, playback or tools."""
import argparse
import json
from pathlib import Path
import time
import urllib.request
import kokoro_speech
from conversation import CHAT_SYSTEM, CHAT_TOOLS, reply_issues
from speech_prefetch import SpeechPrefetch, opening_section


def run(speaker, overlap, prompt):
    cache = SpeechPrefetch(speaker)
    payload = {'model': 'gpt-oss:20b', 'think': 'low', 'stream': True,
               'keep_alive': '15m', 'messages': [
                   {'role': 'system', 'content': CHAT_SYSTEM},
                   {'role': 'user', 'content': prompt}], 'tools': CHAT_TOOLS,
               'options': {'num_ctx': 8192, 'num_predict': 220, 'temperature': 0}}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request('http://127.0.0.1:11434/api/chat',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    start = time.monotonic(); text = ''; calls = []; first = None; final = {}
    try:
        with opener.open(request, timeout=180) as response:
            for line in response:
                item = json.loads(line)
                if item.get('error'): raise RuntimeError(item['error'])
                if item.get('done'): final = item
                message = item.get('message', {})
                text += message.get('content', '')
                calls.extend(message.get('tool_calls', []))
                if text and first is None: first = time.monotonic() - start
                if overlap and not calls: cache.offer(text)
                if calls: cache.clear()
        model_time = time.monotonic() - start
        if calls or reply_issues(text):
            raise RuntimeError('Synthetic reply did not pass the no-tool/advice gate')
        section = opening_section(text, complete=True)
        cache.approve(text)
        audio = cache.take(section) if overlap else None
        hit = audio is not None
        if audio is None: audio = speaker.synthesize(section)
        return {'overlap': overlap, 'first_text_seconds': first,
                'model_seconds': model_time, 'first_audio_ready_seconds': time.monotonic()-start,
                'prefetch_hit': hit, 'audio_bytes': len(audio), 'reply': text,
                'metrics': {k: final.get(k) for k in ('load_duration', 'prompt_eval_duration', 'eval_duration')}}
    finally:
        cache.clear()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    kokoro_speech.ROOT = Path('C:/SimplicityAI-Lab/ThemHands')
    speaker = kokoro_speech.KokoroSpeech()
    results = []
    try:
        speaker.synthesize('Ready.')  # Separate voice initialization from comparison.
        run(speaker, False, 'Say ready.')  # Separate model cold-load cost as well.
        cases = ['For a voice test, explain memory versus storage in two short sentences.',
                 'For a voice test, explain why one DNS timeout cannot establish its cause in two short sentences.']
        for prompt, order in zip(cases, [(False, True), (True, False)]):
            for overlap in order:
                result = run(speaker, overlap, prompt)
                results.append(result)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(results, indent=2), encoding='utf-8')
                print(json.dumps(result), flush=True)
    finally:
        speaker.stop()


if __name__ == '__main__': main()
