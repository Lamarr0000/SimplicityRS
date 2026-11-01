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
    lines = ['Windows file checks — running Windows only: ' + result['windows_directory'],
             'Inside this VM, this checks the VM’s Windows, not your host PC or another drive. No repairs were requested. Windows may write diagnostic logs.']
    lines.extend(result['errors'])
    for item in result['checks']:
        text = item['output'].lower()
        if item['exit_code'] == 0 and 'windows resource protection did not find any integrity violations' in text:
            lines.append('Windows reports that the protected system files passed this verification. That does not rule out other causes of a crash.')
        elif 'windows resource protection found integrity violations' in text:
            lines.append('Windows reports protected-file integrity problems. This verification did not request a repair. Review the detailed log before deciding what to do next.')
        elif item['exit_code'] == 0 and 'no component store corruption detected' in text:
            lines.append('Windows has no component-store corruption flagged in this status check. A full scan has not been performed.')
        else:
            lines.append('This result needs review. SimplicityAI has not established a clean result or a repair from this output.')
        lines.append(item['tool'] + ': command returned exit code ' + str(item['exit_code']) + '. Read the Windows result below; an exit code alone does not prove files are healthy.\n\n' + item['output'] + ('\n' + item['errors'] if item['errors'] else ''))
    lines.append('DISM CheckHealth reads whether corruption has already been flagged; it is not a new full component-store scan. SFC verifyonly checks protected system files without requesting repairs. Neither checks hardware, malware or every Windows problem. If Windows reports corruption or a failed check, keep these results for review before choosing a repair.')
    return '\n\n'.join(lines)
