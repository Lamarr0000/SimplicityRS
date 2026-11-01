"""Fixed read-only health collection and evidence-based screening flags."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def dns_timeout_simulation():
    """Synthetic fixture, deliberately never collected from the running machine."""
    return {'network_status': {
        'simulation': True,
        'adapters': [{'description': 'SIMULATED adapter (not this computer)',
                      'addresses': ['192.0.2.10'], 'gateways': ['192.0.2.254'],
                      'dns_servers': ['192.0.2.1']}],
        'dns_test': {'name': 'example.test', 'server': '192.0.2.1', 'success': False,
                     'checked_utc': 'Synthetic fixture; no query performed'},
        'errors': [], 'changes_made': False}}


def network_report(snapshot):
    """Deterministic evidence report; this is not a model diagnosis."""
    network = snapshot.get('network_status') or {}
    test = network.get('dns_test')
    lines = ['Network check — generated directly from tool evidence, not AI diagnosis.']
    if network.get('simulation'):
        lines.insert(0, 'SIMULATION ONLY — synthetic evidence. No adapter inspection, DNS query, model call or network changes performed.')
    for adapter in network.get('adapters', []):
        lines.append('Adapter: ' + adapter.get('description', 'Unknown'))
        for label, key in [('Addresses', 'addresses'), ('Gateways', 'gateways'), ('Configured DNS', 'dns_servers')]:
            lines.append(label + ': ' + (', '.join(adapter.get(key) or []) or 'Unknown'))
    if test and test.get('success') is True:
        lines.append(f"Succeeded: Windows resolved {test['name']} through configured DNS server {test['server']} at {test['checked_utc']}.")
        lines.append('This result alone gives no reason to change DNS settings.')
    elif test:
        lines.append('The DNS query failed or timed out. Its cause is not established; correlate with symptoms before changing settings.')
        lines.append('Not established: server unreachability, a routing/firewall fault, complete internet failure, or failure of every DNS query.')
        lines.append('Suggested read-only comparison, not executed: in the affected Windows environment, query the same name through an independently known working resolver, if available and permitted, without changing adapter settings. Success would show that alternate query path worked at that time; it would not establish why the original query failed. Failure would leave both paths uncertain, not prove a common cause.')
    else:
        lines.append('DNS query result: Unknown. No successful query was verified.')
    lines.extend('Unknown: ' + error for error in network.get('errors', []))
    lines.append('Not tested: gateway reachability, web/TCP access, IPv6 DNS, other DNS servers, or the host computer. Resolver caches may be used.')
    lines.append('If browsing works and no network symptoms are present, no further investigation is indicated by this limited check. Otherwise, describe the failing application and time of failure.')
    lines.append('No settings changed.')
    return '\n\n'.join(lines)


def screening(snapshot):
    """Transparent thresholds, not diagnoses. Preserve missing data as unknown."""
    flags = []
    memory = snapshot.get("memory")
    if memory:
        percent, available = memory.get("available_percent"), memory.get("available_gib")
        if percent is not None and available is not None and (percent < 10 or available < 2):
            flags.append({"area": "Memory", "finding": "Low available memory at collection time",
                          "evidence": f"{available} GiB available ({percent}%)",
                          "next_check": "Check which applications are using memory before considering hardware changes."})
    for volume in snapshot.get("volumes", []):
        percent, free = volume.get("free_percent"), volume.get("free_gib")
        if percent is not None and free is not None and (percent < 10 or free < 20):
            flags.append({"area": f"Drive {volume['drive']}", "finding": "Limited free-space headroom",
                          "evidence": f"{free} GiB free ({percent}%)",
                          "next_check": "Review storage usage and confirm what can safely be moved or removed. Nothing was deleted."})
    events = snapshot.get("system_events")
    if events and events.get("sampled_count", 0):
        flags.append({"area": "System events", "finding": "Recent Critical/Error events need symptom correlation",
                      "evidence": f"{events['sampled_count']} sampled events in the last {events['window_days']} days",
                      "next_check": "Match event times and providers to the user's symptoms. Event counts alone do not prove hardware failure."})
    return flags


def collect_health():
    exe = Path(os.environ["WINDIR"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    script = (ROOT / "Collect-Health.ps1").read_text(encoding="utf-8")
    env = dict(os.environ)
    # A parent PowerShell 7 session may pass an incompatible module search
    # path to Windows PowerShell 5.1. Let the child construct its native path.
    env.pop("PSModulePath", None)
    # Fixed script passed on stdin, never a model-generated command. A short
    # child process makes no policy changes and cannot accept model arguments.
    result = subprocess.run([str(exe), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, encoding="utf-8-sig", errors="replace", timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW, check=False, env=env)
    if result.returncode:
        raise RuntimeError("Read-only health collector failed: " + result.stderr[-1200:])
    snapshot = json.loads(result.stdout.strip())
    if snapshot.get("schema") != 1:
        raise RuntimeError("Unexpected health snapshot format")
    snapshot["screening_flags"] = screening(snapshot)
    snapshot["limitations"] = [
        "This is a screening snapshot, not a full diagnosis or repair.",
        "It does not test disk surface/SMART health, filesystem integrity, malware, temperatures, or offline Windows.",
        "Event message excerpts may contain machine, account or network identifiers; review logs before sharing. No Security log or recovery keys requested.",
        "No repairs or system-setting changes performed; results are saved in ThemHands local logs.",
    ]
    return snapshot
