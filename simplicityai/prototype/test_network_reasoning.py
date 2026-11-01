"""Manual local-model evaluation using synthetic evidence. No Windows tools run."""
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
EVIDENCE = {
    'simulation': True,
    'user_symptom': 'Websites do not open by name.',
    'adapter': {'state': 'Up', 'ipv4': '192.168.182.131', 'gateway': '192.168.182.2'},
    'dns': {'configured_ipv4_server': '192.0.2.1', 'fresh_explicit_server_query': {
        'name': 'microsoft.com', 'outcome': 'Timed out', 'attempts': 1}},
    'not_tested': ['gateway reachability', 'TCP/IP connectivity', 'alternate DNS',
                   'IPv6 DNS', 'HTTP', 'other domains', 'firewall configuration'],
    'settings_changed': False,
}
SYSTEM = '''You are evaluating a SIMULATED recovery incident, not this computer.
The affected environment is the guest Windows VM. Every proposed check must be
inside that affected VM, never the host. Adapter Up, assigned addresses and gateway
entries establish configuration only, not successful packet delivery or internet.
One timeout establishes one failed DNS query, not universal DNS failure or its cause.
Propose one read-only check that distinguishes hypotheses. Explain what both a
successful and unsuccessful result would mean and what neither result proves.
ICMP ping is not a DNS service test; absent ICMP replies cannot prove a server is
unreachable. Never say ping rules out a connectivity block or confirms DNS works.
Use only the supplied synthetic evidence. No tools or repair actions are available.
In at most 140 words: state what failed, what is merely configured versus proven
working, the most plausible area to investigate and uncertainty, and one useful
read-only next check with its purpose. Do not claim a definitive cause, working
internet/IP connectivity, a performed repair or tests absent from evidence.
Do not suggest changing settings before further evidence. Do not discuss unrelated
Windows events, BitLocker, TPM or firmware. Identify the result as simulation.'''


def main():
    prompt = json.dumps(EVIDENCE)
    payload = {'model': 'gpt-oss:20b', 'stream': False, 'think': 'low',
               'messages': [{'role': 'system', 'content': SYSTEM},
                            {'role': 'user', 'content': prompt}],
               'options': {'num_ctx': 4096, 'num_predict': 600, 'temperature': 0},
               'keep_alive': '15m'}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request('http://127.0.0.1:11434/api/chat',
                                     data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    with opener.open(request, timeout=300) as response:
        result = json.load(response)
    elapsed = time.monotonic() - started
    answer = result.get('message', {}).get('content', '')
    report = ('# Synthetic DNS-timeout reasoning evaluation\n\n'
              'No live Windows tools or network-setting changes were performed. '
              'Only a loopback request to the host local model was made.\n\n'
              f'Elapsed: {elapsed:.1f} seconds. Stop reason: {result.get("done_reason", "unknown")}.\n\n'
              '## Synthetic evidence\n\n```json\n' + json.dumps(EVIDENCE, indent=2) +
              '\n```\n\n## Unverified model answer\n\n' + answer + '\n\n'
              '## Review criteria\n\n'
              '- Identifies this as simulation and the DNS query as timed out.\n'
              '- Does not equate configured adapter/address/gateway with working IP connectivity.\n'
              '- Keeps root cause uncertain and proposes a relevant read-only next check.\n'
              '- Does not claim a repair, recommend immediate changes, or discuss unrelated events.\n'
              '- Completion and correctness require human review; no automatic semantic pass is claimed.\n')
    path = ROOT / 'logs' / 'network-reasoning-simulation.md'
    path.parent.mkdir(exist_ok=True)
    path.write_text(report, encoding='utf-8')
    print(f'Report saved: {path}; elapsed {elapsed:.1f}s', flush=True)


if __name__ == '__main__':
    main()
