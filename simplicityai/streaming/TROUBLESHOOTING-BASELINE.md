# SimplicityAI troubleshooting baseline

This baseline is integrated into the isolated Voice Pilot. It is a general Windows troubleshooting toolkit, not a collection of demonstrations that require users to select a tool. Launcher integration can follow separately.

## Architecture

One local conversational agent uses an embedded troubleshooting skill library, an authoritative registered-tool catalog and ThemHands execution. Additional model agents are not required for these checks. Keeping a single reasoning model avoids unnecessary competition for the host's RAM/GPU.

- Symptom guidance maps storage, devices/drivers, performance, startup/crashes, networking and security/update questions to appropriate tools.
- Explicit requests to check a named diagnostic area are routed to fixed collectors before the model answers. The model can request a relevant follow-up query, including a literal device/provider filter.
- Results contain scope, time, available/unknown status, bounds and limitations. Tool evidence precedes claims; actions are followed by observations. Completed reports cannot promise a check that was never performed.
- Diagnostic evidence is bounded for the local model. Omitted rows are marked; the full collected result remains in the local evidence log. The newest complete conversational exchanges are retained within the model context budget.
- Existing desktop assistance, cancellation, user input takeover, CPU sampling, file creation and recorded-conversation export remain connected.

## Connected baseline

| Need | Available tools and evidence | Important limit |
|---|---|---|
| OS, RAM, CPU and graphics inventory | `inspect_windows(system)` using Windows CIM | Inventory is not a hardware stress test |
| Free space, disks and partitions | `inspect_windows(storage)`; calculated bytes, GB, GiB and percentage; storage-provider status | Low space is not disk failure; provider status is not comprehensive SMART/surface testing |
| Device Manager problems | `inspect_windows(devices)`; problem codes, device classes and IDs, problem count | A device code must be interpreted; inventory can be truncated |
| Installed drivers | `inspect_windows(drivers, query=...)`; version, provider, date, signing and INF | Not an online update search or driver installation; no match alone does not prove absence |
| Busy processes | `get_cpu_process_snapshot`; bounded CPU-time sample and ranking | Not lifetime load, memory ranking, or identical to Task Manager CPU Utility |
| Service state | `inspect_windows(services)`; start mode, state and exit code | A stopped automatic service may be normal; no service changes |
| Crashes and errors | `inspect_windows(events)`; recent bounded System/Application events with provider, ID, UTC time and message excerpt | Historical errors do not establish the cause; excerpts and sample windows are bounded |
| Updates | `inspect_windows(updates)`; recorded hotfixes and recent update failures | Not complete update history, an online scan, or an installation |
| Startup and boot clues | `inspect_windows(startup)`; startup names, power/battery status and read-only current BCD query | No boot-file integrity claim; access may require elevation |
| Protected Windows files | Existing `verify_windows_files`: SFC verification and DISM recorded-health check | Administrator permission and confirmed current Windows required; no repair and no offline installation inspected |
| Encryption and security status | `inspect_windows(security)`; BitLocker status, TPM, Secure Boot, Defender state | No recovery keys collected; denied/unsupported checks stay unknown; Defender status is not a malware scan |
| Network and website symptoms | Existing network/DNS tool plus Edge launch and actual page observation | DNS success is not proof of web access; no network reset |
| Windows utility windows | Fixed launch catalog: Task Manager, Device Manager, Disk Management, Event Viewer, Services, System Information, Reliability Monitor, Settings, Explorer, Notepad, Calculator and Edge | Launch is not proof that the window works. Administrative MMC controls are observation-only in this pilot |
| Desktop assistance | Observe accessible controls, switch windows, click, type and scroll; new text files; transcript export | Not visual interpretation of every custom control; arbitrary shell/file operations are not exposed |

## Collector implementation

`Inspect-Windows.ps1` is an application-owned fixed read-only collector. Its nine categories are validated. Query text is a literal filter passed through environment data, never interpolated as PowerShell code. The wrapper runs the fixed collector text in Windows PowerShell with no persistent or process execution-policy modification. Inherited PowerShell module paths are removed from the child environment to avoid mixing incompatible module versions. Native .NET event readers avoid the host's blocked Diagnostics module. Each section catches provider/permission failures separately. The owned process has a timeout and cooperative cancellation.

This does not clone Codex's private runtime or confer the same model intelligence. It supplies broader diagnostics, desktop tools and reusable troubleshooting skills to the local model. Current running Windows is the only connected diagnostic target, even when that Windows is a VM. Offline Windows, physical disk stress tests, dump analysis, malware scanning, driver installation, boot repair, cloning and restoration are not validated or enabled by this baseline.

## Verification

- All nine categories were exercised read-only on the host. OS/storage/devices/drivers/services/update records/TPM/Defender/startup/battery data returned. Events initially exposed a module-loading problem; the native event reader then returned System/Application/update records successfully.
- Secure Boot and current boot configuration were denied in the unelevated test; those results were correctly marked unknown. No elevation, repair, security change, driver install, process termination or disk modification was attempted.
- Automated tests cover argument isolation, cancellation, scope, skill routing, output bounds and existing pilot behavior. Local-model scenario tests use synthetic records and do not prove diagnosis of a real broken computer.
- Full local probe evidence: the StreamingPrototype logs folder, `baseline-*.json`. These may contain local device details and are not committed.

Exit/reopen **SimplicityAI Voice Pilot** to load the baseline. A useful first test is a request to check device problems, driver records and available drive space, explaining findings without changing anything. Then use an actual reported symptom rather than testing every utility individually.
