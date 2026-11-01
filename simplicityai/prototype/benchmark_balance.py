"""Bounded, sequential synthetic CPU-thread comparison; no tools or microphone.

Keeps the production model/context. Records cold and warm runs separately and
restores default runner options in finally. Does not alter app configuration.
Run while the assistant is idle; results are host-specific, not a quality test.
"""
import argparse
import json
from pathlib import Path
import time
import urllib.request


def request(threads, prompt):
    options = {'num_ctx': 8192, 'num_predict': 100, 'temperature': 0}
    if threads is not None:
        options['num_thread'] = threads
    payload = {'model': 'gpt-oss:20b', 'think': 'low', 'stream': True,
               'keep_alive': '15m', 'options': options,
               'messages': [{'role': 'system', 'content':
                   'Answer the synthetic question in one brief sentence. No actions.'},
                   {'role': 'user', 'content': prompt}]}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request('http://127.0.0.1:11434/api/chat',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    start = time.monotonic()
    first = None
    final = {}
    text = ''
    with opener.open(req, timeout=180) as response:
        for line in response:
            part = json.loads(line)
            if part.get('error'):
                raise RuntimeError(part['error'])
            chunk = part.get('message', {}).get('content', '')
            if chunk and first is None:
                first = time.monotonic() - start
            text += chunk
            if part.get('done'):
                final = part
    duration = final.get('eval_duration', 0) / 1e9
    return {'threads': threads or 'automatic', 'first_text_seconds': first,
            'elapsed_seconds': time.monotonic() - start,
            'tokens_per_second': final.get('eval_count', 0) / duration if duration else None,
            'reply': text, 'done_reason': final.get('done_reason'),
            'metrics': {k: final.get(k) for k in ('load_duration', 'prompt_eval_count',
                'prompt_eval_duration', 'eval_count', 'eval_duration')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for threads in (None, 4, 8):
            for phase, prompt in (
                ('warmup', 'Say ready.'),
                ('measured', 'What is the difference between memory and storage?'),
                ('measured', 'Does one failed DNS query prove the internet is broken?')):
                result = request(threads, prompt)
                result['phase'] = phase
                results.append(result)
                args.output.write_text(json.dumps(results, indent=2), encoding='utf-8')
                print(json.dumps(result), flush=True)
    finally:
        # Runner options can reload the model; return to the app's default setup.
        restored = request(None, 'Say ready.')
        print(json.dumps({'default_restore': restored}), flush=True)


if __name__ == '__main__':
    main()
