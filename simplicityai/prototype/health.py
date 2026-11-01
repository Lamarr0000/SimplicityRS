"""Fixed read-only health collection and evidence-based screening flags."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


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
