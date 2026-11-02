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


## November 1: recovery-context, interrupted findings and table correction

User supplied the latest exported conversation. Log showed recovery/affected-Windows confusion, unsupported driver freshness claims, generic emoji/boilerplate replies, and lost findings. Storage/device/driver/event collection finished in a request that was then interrupted by new voice input before Conversation.finish, so later table requests had no facts in normal model history. Viewer launch was attempted twice but the old exception path did not log its result; elevation cause is not established from that log.

Added session-owned recent_findings independent of completed model turns, get_recent_findings, immediate scoped tables, copy including all values, and direct cached-table recall without recollecting or model reconstruction. Baseline and CPU findings enter the recorded transcript as measured-fact cards. Interrupted visible replies and interrupted user requests are retained; New chat clears facts and preferences, reopening remains fresh. Cached model excerpts are bounded.

Recovery-boot descriptions now keep an unbooted affected Windows separate from current-Windows diagnostics until explicit local-target confirmation. Local desktop viewer actions remain distinct and can open in the recovery environment; explicit outside-host actions remain blocked. This does NOT add offline Windows inspection. The local-model replay held offline scope, blocked current collectors, and opened a simulated local Device Manager.

Fixed viewer requests have an app-owned launch/observe route. Normal Popen elevation-required errors for known viewers can fall back to Windows ShellExecute open, allowing Windows to present its normal permission prompt. No prompt was approved, suppressed or bypassed and no real administrative viewer launched during development. Errors are now logged as observations. Viewer GUI verification still needs the user's live test.

Removed assistant emoji at generation and speech boundaries; preserved arithmetic symbols. Driver reports cannot infer up-to-date from installed records. Conversation exports honor explicit requested filenames without overwriting. Primary issue no longer sticks to a greeting.

54 Python regression checks and client voice/table/copy checks pass. Seven baseline, five desktop and three recovery-scope local-model cases pass using simulated observations. They do not certify general reasoning. No app restarted. Next user: Exit/reopen Voice Pilot; collect current-Windows storage/device facts and ask for the drive table again after an interruption. Offline Windows diagnosis remains a major missing capability; do not hide it with recovery-OS results.


## November 1: live multi-turn controller regressions

User's new conversation exposed repeated target/permission loops, cancelled actions resuming, incomplete spoken fragments replacing tasks, taskbar controls mistaken for app controls, and fragile close/minimize behavior. This was a coverage gap in the earlier isolated scenario tests. New regression source is the actual multi-turn sequence, not just short independent prompts.

Target binding now accepts Windows installation that is running Simplicity A I, computer that's running it, and explicit this computer when no offline target is selected; negatives/outside targets remain blocked. General diagnostic requests route to the baseline after confirmation instead of asking permission repeatedly. A plain confirmation gets an app-owned acknowledgement and useful startup follow-up; a model cannot re-ask the confirmed target indefinitely. Greeting-only introductions no longer become the original fault.

Cancellation (never mind/forget it/don't even worry about it) is handled before model/tool execution, clears pending plans and pauses mutating tool actions until a new explicit request. Voice continuations within a short window retain the original incomplete request. Basic spoken/numeric two-operand arithmetic routes directly to the existing real-Calculator verified-button/display tool; multi-operation expressions are not partially evaluated.

Added observed-window identity tools: list_windows and manage_window, normal WM_CLOSE/minimize only, no process killing or unsaved-prompt dismissal. Exact pilot runtime executable identifies the real SimplicityAI window, rather than the VMware window with a similar title. Missing/ambiguous identity prevents action. Explicit close-browser and minimize-others workflows use these primitives and verify outcomes. UIA control IDs are now restricted to the foreground application tree; background Taskbar buttons cannot masquerade as Calculator controls. Semantic fingerprints ignore tree-drawing prefixes while still checking coordinates/control details and foreground state.

64 Python regression checks and existing voice/table client checks pass. Nine-step simulated replay covers startup issue -> this-computer confirmation -> explicit diagnostic -> cancel -> browser open/close -> minimize others -> 1+1. No live window was closed/minimized during development; read-only enumeration saw no pilot native process (user had closed it), so minimize/close live verification remains for user. No app restarted. Normal Windows/security/VM/BRS settings unchanged.

Next action: reopen Voice Pilot and retry a normal multi-step conversation. Do not call this production-ready based on a simulated replay; collect the next live log. Offline Windows inspection remains outside this pilot.

Follow-up: existing seven diagnostic and five desktop model replays also pass. Calculator foreground activation is attempted only for the exact HWND returned by its verified tool, with ordinary APIs and an explicit failure report; not live-tested here. Speech preparation strips Markdown emphasis/link formatting without altering arithmetic operators. No window-management live actions occurred.
