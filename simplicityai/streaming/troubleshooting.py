"""Embedded troubleshooting skills: symptoms -> tools -> evidence -> next step."""
import re

BASE=('Use relevant connected tools proactively; the user need not name or activate them. '
      'Do not send the user to do a manual check that a connected collector can perform; explain a permission/provider blocker instead. '
      'Prefer fixed read-only collectors for facts and desktop controls to inspect apps. '
      'Explain the check briefly, collect real evidence, distinguish findings from possible causes, '
      'and choose the next useful check. Do not run every tool on every question. '
      'Missing, denied, unsupported or truncated data is unknown, never a clean bill of health. '
      'Current Windows may be a VM; never imply its results describe an outside host or offline disk. '
      'Never claim a drive is physically failing, a driver is missing, or boot files are corrupt '
      'without supporting evidence. Read-only checks do not authorize disk/security changes. '
      'No destructive repair, recovery-key collection, driver installation or service termination is exposed.')

SKILLS=[
 (r'\b(?:disks?|drives?|storage|space|partition|ssd|hard.?drive)\b',
  'Storage: inspect_windows(storage) for disks, volumes, free bytes, partitions and provider health. '
  'Low free space is not disk failure; provider OK is not a full SMART/surface test. Correlate storage-related events '
  'For a fixed Windows volume, free space below 10 percent or 20 GiB needs review; do not describe 4.3 percent as sufficient. '
  'Use the collector-calculated GB/GiB/percent fields exactly rather than converting raw bytes mentally. '
  'using inspect_windows(events) and symptoms. Open Disk Management if requested for visual inspection. '
  'Do not format, initialize, run repair CHKDSK or clone disks.'),
 (r'driver|device|usb|bluetooth|audio|sound|wi.?fi|display|printer',
  'Devices/drivers: inspect_windows(devices) for device problem codes, then inspect_windows(drivers, query=<device name>) '
  'for installed version/provider/signing. A problem code or missing matching record needs interpretation; an old date '
  'does not prove an outdated or missing driver. Do not install/uninstall/disable devices. Open Device Manager if useful.'),
 (r'slow|cpu|processor|memory|ram|performance|freez|task.?manager',
  'Performance: get_cpu_process_snapshot for a bounded current CPU ranking; inspect_windows(system) and storage '
  'for memory/OS/hardware and headroom. Use Task Manager for visual confirmation if asked. '
  'A single high-CPU sample is not a fault and differs from memory usage. Do not terminate processes.'),
 (r'crash|restart|blue.?screen|error|hang|boot|start.?up|start|corrupt',
  'Crashes/startup: inspect_windows(events), system, startup or services as relevant. Match provider/event ID/time/message '
  'to the symptom, not just error counts. verify_windows_files performs SFC verification and DISM recorded-health check '
  'in confirmed running Windows with admin permission; it does not repair files. An unbootable/offline Windows '
  'installation is not inspected by current-Windows checks. Boot-file corruption cannot be inferred from a generic event.'),
 (r'network|internet|browser|website|dns|connect',
  'Networking: existing get_network_snapshot reads configuration and a bounded DNS test in confirmed running Windows. '
  'DNS success does not prove web access; use Edge HTTPS launch and actual page observation for a browser test. '
  'Distinguish app launch failure from website failure. No adapter/DNS resets.'),
 (r'update|bitlocker|tpm|secure.?boot|security|malware|virus',
  'Updates/security: inspect_windows(updates) for recorded hotfixes and recent failure events; no online update scan. '
  'inspect_windows(security) for status only; unavailable elevated/provider checks stay unknown. '
  'Defender status is not a malware scan. Never collect recovery keys or disable security.'),
]


def guidance(prompt):
    matches=[text for pattern,text in SKILLS if re.search(pattern,prompt,re.I)]
    return BASE+('\nRelevant troubleshooting skills:\n'+'\n'.join(matches[:3]) if matches else '')


def requested_checks(prompt):
    if re.search(r"\b(?:do not|don't|no need to)\s+(?:check|inspect|review|find|verify|look)\b",prompt,re.I):return set()
    if re.search(r'\b(?:driver status|status of (?:my |the |these |installed )?drivers)\b',prompt,re.I):return {'devices','drivers'}
    if (re.search(r'\bdrivers?\b.{0,40}\b(?:good|okay|ok|working|healthy|up.to.date)\b',prompt,re.I)
            and re.search(r'\b(?:my|this|these|installed)\b',prompt,re.I)):
        return {'devices','drivers'}
    if not re.search(r'\b(check|inspect|review|find|verify|look|list)\b',prompt,re.I):
        if re.search(r'\b(?:my|this)\b',prompt,re.I):
            if re.search(r'out of (?:disk )?space|running low on space|disk (?:is )?full|drive (?:is )?full',prompt,re.I):return {'storage'}
            if re.search(r'computer (?:is |has been |keeps )?(?:slow|freezing|crashing)|pc (?:is )?slow',prompt,re.I):return {'system','storage','events'}
            if re.search(r'driver.{0,25}missing|missing.{0,25}driver|device.{0,25}(?:not working|stopped working)',prompt,re.I):return {'devices','drivers'}
        return set()
    required=set()
    for pattern,areas in [
        (r'\b(?:free space|storage|drives?|disks?)\b',{'storage'}),
        (r'device.?manager|device problem',{'devices'}),
        (r'driver',{'devices','drivers'}),
        (r'error|event|restart|crash',{'events'}),
        (r'service',{'services'}),
        (r'startup|start.?up|boot configuration',{'startup'}),
        (r'bitlocker|tpm|secure.?boot|defender',{'security'}),
        (r'update',{'updates'})]:
        if re.search(pattern,prompt,re.I):required.update(areas)
    return required


def completed_report(text):
    """Do not turn collected findings into a promise of work that never ran."""
    return re.sub(r"\b(?:Let me|Let['’]s|I(?: will|'ll))\s+(?:check|inspect|review|open|run|look|verify)\b[^.!?]*(?:[.!?]|$)",'',text,flags=re.I).strip()


def diagnostic_report_issue(text,areas):
    for sentence in re.split(r'[.!?\n]',text):
        if re.search(r"\b(?:not|cannot|can't|doesn't|don't|no)\b",sentence,re.I):continue
        if 'drivers' in areas and re.search(r'up[ -]to[ -]date|all.{0,20}drivers.{0,30}(?:signed|healthy|working)|drivers?.{0,80}(?:functioning correctly|working correctly|properly signed|properly installed|healthy)',sentence,re.I):
            return 'Installed driver records do not establish that drivers are up to date or that all drivers work. Report only returned versions, signing fields and problem codes; update availability was not checked.'
        if 'updates' in areas and re.search(r'\b(?:updates?|patches?)\b.{0,35}\b(?:available|ready to install)\b|\b(?:available|pending)\b.{0,35}\b(?:updates?|patches?)\b',sentence,re.I):
            return 'Only recorded installed hotfixes and historical failure events were checked. Online update availability and pending updates were NOT checked. Correct the report without implying an update is available.'
    return None
