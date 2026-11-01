"""Sequential synthetic local inference benchmark; no Windows diagnostic tools."""
import json
from pathlib import Path
import time
import urllib.request

CASES = [
    {'case': 'timeout', 'simulation': True, 'environment': 'affected Windows VM',
     'evidence': 'Adapter Up; address and gateway configured. One explicit-server DNS A query timed out.',
     'unknown': 'Packet delivery, gateway reachability, DNS service availability, firewall, web access.'},
    {'case': 'success', 'simulation': True, 'environment': 'affected Windows VM',
     'evidence': 'One explicit-server DNS A query succeeded. User reports no symptoms.',
     'unknown': 'Web access, other resolvers, IPv6 DNS, historical failures.'},
]
SYSTEM = '''Review synthetic evidence only. Never perform actions. Return JSON with
observed, unknown, next_check fields, each a short string; at most 80 words total.
State only what the test proves. Configured is not working; a timeout does not prove
unreachability or a cause. DNS success does not prove web access. If no symptoms and
the test succeeded, say no further check indicated by this evidence. Otherwise offer
one read-only comparison inside the affected VM, with limits on its interpretation.
No repairs, firmware suggestions or host checks. No invented results.'''


def main():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    runs = []
    for context in (2048, 4096):
        for case in CASES:
            payload = {'model': 'gpt-oss:20b', 'stream': False, 'think': 'low',
                       'format': 'json', 'keep_alive': '15m',
                       'messages': [{'role': 'system', 'content': SYSTEM},
                                    {'role': 'user', 'content': json.dumps(case)}],
                       'options': {'num_ctx': context, 'num_predict': 350, 'temperature': 0}}
            start = time.monotonic()
            request = urllib.request.Request('http://127.0.0.1:11434/api/chat',
                       data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            with opener.open(request, timeout=300) as response:
                result = json.load(response)
            elapsed = time.monotonic() - start
            answer = result.get('message', {}).get('content', '')
            try:
                parsed = json.loads(answer)
                valid = set(parsed) == {'observed', 'unknown', 'next_check'} and all(isinstance(v, str) for v in parsed.values())
            except (ValueError, TypeError):
                valid = False
            run = {'context': context, 'case': case['case'], 'elapsed_seconds': round(elapsed, 2),
                   'done_reason': result.get('done_reason'), 'format_valid': valid,
                   'eval_count': result.get('eval_count'),
                   'eval_duration_ns': result.get('eval_duration'),
                   'load_duration_ns': result.get('load_duration'), 'answer': answer}
            runs.append(run)
            path = Path(__file__).resolve().parent / 'logs' / 'reasoning-benchmark.json'
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps({'synthetic': True, 'system': SYSTEM, 'cases': CASES, 'runs': runs}, indent=2), encoding='utf-8')
            print(f"ctx={context} case={case['case']} elapsed={elapsed:.1f}s format={valid} stop={run['done_reason']}", flush=True)


if __name__ == '__main__':
    main()
