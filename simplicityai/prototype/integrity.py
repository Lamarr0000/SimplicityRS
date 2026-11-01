"""Fixed verification tools for running Windows. Never accepts model commands."""
import ctypes
import os
from pathlib import Path
import subprocess
import time


def is_admin():
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def collect_integrity(emit, check_stop):
    target = str(Path(os.environ['SystemRoot']))
    result = {'scope': 'Running Windows only', 'windows_directory': target,
              'repair_requested': False, 'checks': [], 'errors': []}
    if not is_admin():
        result['errors'].append('Administrator permission is required. No checks ran. Stop SimplicityAI, then use Start-SimplicityAI-Admin.cmd inside the VM and approve Windows permission prompt.')
        return result
    system = Path(target) / 'System32'
    for name, command in [('Windows component-store status', [str(system / 'dism.exe'), '/Online', '/Cleanup-Image', '/CheckHealth']),
                          ('Protected Windows file verification', [str(system / 'sfc.exe'), '/verifyonly'])]:
        check_stop()
        emit('action', f'{name}: checking {target}, the Windows currently running. No repair option requested. This may take several minutes; Stop will prevent the next check after this command finishes.')
        start = time.monotonic()
        process = subprocess.run(command, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        def decode(data):
            return data.decode('utf-16-le' if b'\x00' in data[:200] else 'oem', errors='replace').strip()
        item = {'tool': name, 'arguments': command[1:], 'exit_code': process.returncode,
                'elapsed_seconds': round(time.monotonic()-start, 1),
                'output': decode(process.stdout), 'errors': decode(process.stderr)}
        result['checks'].append(item)
        emit('observation', __import__('json').dumps(item, ensure_ascii=False))
    return result


def integrity_report(result):
    lines = ['Windows file check results',
             'Checked: the Windows currently running at ' + result['windows_directory'] + '. If running inside a VM, this checks the VM, not the host PC. Other Windows installations were not checked.']
    lines.extend(result['errors'])
    passed = 0
    for item in result['checks']:
        text = item['output'].lower()
        if item['exit_code'] == 0 and 'windows resource protection did not find any integrity violations' in text:
            lines.append('Windows reports that the protected system files passed this verification. That does not rule out other causes of a crash.')
            passed += 1
        elif 'windows resource protection found integrity violations' in text:
            lines.append('Windows reports protected-file integrity problems. This verification did not request a repair. Review the detailed log before deciding what to do next.')
        elif item['exit_code'] == 0 and 'no component store corruption detected' in text:
            lines.append('Windows has no component-store corruption flagged in this status check. A full scan has not been performed.')
            passed += 1
        else:
            lines.append('This result needs review. SimplicityAI has not established a clean result or a repair from this output.')
    if len(result['checks']) == 2 and passed == 2 and not result['errors']:
        lines.append('What to do next: these checks found no reason to repair Windows files. If the computer still has a problem, describe what happens and when so we can choose a different check.')
    elif result['checks']:
        lines.append('What to do next: review the tool evidence before choosing a repair. A failed or unclear check does not by itself identify the cause.')
    lines.append('No repairs were requested. These checks do not rule out hardware problems, malware, application faults or every cause of a crash. Full Windows output and progress details remain in Activity and tool evidence and the local logs.')
    return '\n\n'.join(lines)
