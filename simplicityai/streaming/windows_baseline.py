"""Fixed read-only Windows diagnostic categories, not model-authored commands."""
import json
import base64
import os
from pathlib import Path
import subprocess
import time
from desktop_tools import definition

AREAS=['system','storage','devices','drivers','services','events','updates','security','startup']
BASELINE_TOOLS=[definition('inspect_windows','Read a focused Windows troubleshooting category using fixed local Windows queries. Choose area: system=OS/hardware/RAM/GPU; storage=free space/disks/partitions/provider health; devices=Device Manager inventory/problem codes; drivers=installed versions/signing, NOT online updates; services=status; events=recent bounded errors/messages; updates=recorded hotfixes/failure events; security=BitLocker/TPM/Secure Boot/Defender status only; startup=startup names and battery. Optional query filters records literally. Current Windows only, no repairs or changes.',
    {'area':{'type':'string','enum':AREAS},'query':{'type':'string','maxLength':80}},('area',))]


def inspect_windows(area,query,check_stop):
    if area not in AREAS or not isinstance(query,str) or len(query)>80:raise ValueError('Unsupported diagnostic category or query')
    check_stop()
    executable=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    # Run our fixed collector text as a command, like the existing health
    # collector. No execution-policy change and no model-authored PowerShell.
    script=Path(__file__).with_name('Inspect-Windows.ps1').read_text(encoding='utf-8')
    command='& {\n'+script+'\n} -Area $env:SIMPLICITY_INSPECT_AREA -Query $env:SIMPLICITY_INSPECT_QUERY'
    encoded=base64.b64encode(command.encode('utf-16le')).decode('ascii')
    env=dict(os.environ,SIMPLICITY_INSPECT_AREA=area,SIMPLICITY_INSPECT_QUERY=query)
    env.pop('PSModulePath',None)  # Do not load PowerShell 7 modules into Windows PowerShell.
    process=subprocess.Popen([str(executable),'-NoProfile','-NonInteractive','-EncodedCommand',encoded],env=env,
                             stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+35
    try:
        while True:
            check_stop()
            try:output,error=process.communicate(timeout=.1);break
            except subprocess.TimeoutExpired:
                if time.monotonic()>deadline:raise TimeoutError('Windows collector timed out; results unavailable')
        if process.returncode:raise RuntimeError('Windows collector failed: '+error.decode('utf-8',errors='replace')[:600])
        if len(output)>250000:raise ValueError('Collector exceeded its output bound')
        return json.loads(output.decode('utf-8-sig'))
    finally:
        if process.poll() is None:process.terminate();process.communicate(timeout=5)
