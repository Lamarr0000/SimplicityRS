# Offline streaming conversation prototype

Isolated development build, November 1, 2026. **Not promoted over host 0.6.3.**
No VM transfer or replacement of the working installation was performed.

## What changed

The client sends 512-sample, 16 kHz mono PCM frames over an authenticated loopback
WebSocket. A persistent CPU worker runs Silero speech detection and online
Zipformer decoding during the utterance. Partial text is displayed but never
executed. The endpoint uses about 640 ms of nonspeech and preserves input pre-roll.
Long utterances require review; existing short-word Whisper fallback remains.

Native Ollama tool calls still pass through the existing ThemHands argument,
target and expression checks. Conversation output is divided into bounded useful
segments while generation continues, then synthesized by the persistent fixed
Kokoro af_heart worker. Audio is transported as small PCM packets. Synthesis is
still whole-segment ONNX inference, not a native speech-to-speech model.

One session controller owns turn IDs, cancellation, capture generations and bounded
queues. Speech detection pauses playback without cancelling a backend task.
Recognized replacement input cancels a pending model turn cooperatively; an
already-running action may finish. Explicit continue/resume requests resume the
retained playback queue; new requests clear it. The client tracks playback offsets.
New chat clears active history and target binding. Nothing automatically resumes
saved logs. Warm speech/model initialization precedes the Ready indication.

The dedicated window is adapted from **our own** existing WebView2 window source,
using port 8770 and a separate browser profile. No installed Codex/ChatGPT source
was copied. Exit and closing the window stop the owned prototype service/process
trees. They do not stop the shared Ollama service or the working app on port 8769.

## Measured decision

A paced synthetic voice test, with no microphone or physical playback, produced:

| Stage | Seconds |
|---|---:|
| End of synthetic speech to final transcript | 0.733 |
| Final transcript to completed model answer | 4.219 |
| First useful segment synthesis | 2.768 |
| End of speech to useful PCM available to client | **7.723** |

The model's first content token arrived about 2.14 seconds after submission, but
the short one-sentence answer did not reach a segment boundary until completion.
Model metrics: prompt evaluation 0.574 s, 32 generated tokens in 3.604 s, load
0.006 s. The response was a useful explanation of RAM, not an acknowledgment.
This is one warm synthetic case, not an average, guarantee or heard-latency test.

The first native-tool typed test took 16.0 s to prepare its first audio, including
7.96 s prompt evaluation and 4.26 s first-segment synthesis. Its prompt differed
from the voice test, so those results do not establish a controlled speedup.
The second entry in the original typed benchmark included stale audio from the
prior turn and is **excluded**. The benchmark now filters events by turn ID.

An earlier voice run transcribed RAM as “our AM” and elicited a clarification.
Its initial “Sure!” was not a useful reply and is not counted as success.
The measurement now distinguishes useful audio from generic acknowledgments.
The repeat decoded “R A M” correctly. Recognition remains variable.

**Decision: do not promote yet.** The 2–3 second target was missed. Speech
recognition now finishes quickly; model generation and Kokoro inference dominate
this case. These measurements do not isolate CPU contention, GPU offload or memory
bandwidth. The next substantial experiment should compare model/runtime choices
against recovery-tool quality and latency, rather than continue UI tweaks.

Ten other synthetic phrases produced partials before finalization and preserved
important negations and stop/cancel wording. Some spelling errors remained
(“internet”/“website”, split “update”). No real microphone, echo, cough, accent,
physical speaker, Windows app interaction or interruption UX was tested here.
The window compiles; live native-window QA is pending.

## Reporting limits

The original full-answer gate is replaced by progressive narrow phrase checks.
Those checks do **not** verify factual truth. A problematic later sentence cannot
retract earlier spoken audio. Late mixed speech/tool output stops the turn; hard
tool validation still prevents unsupported tool execution. This is one reason
the build remains isolated. No arbitrary commands, repair tools or offline-Windows
inspection were added.

JSON-schema-constrained and prompt-only JSON decision experiments returned empty
answers with installed gpt-oss/Ollama. They were rejected; native tool calling was
retained. No internal reasoning tokens were displayed, spoken or saved.

## Host development use

All runtime paths/dependency versions and Silero provenance are recorded in
`runtime-manifest.json`. Reuses existing downloaded ASR, Kokoro and local Ollama
weights. New dependencies live under `C:\SimplicityAI-Lab\StreamingPrototype`.
Model files/runtime packages are excluded from Git. This is not a portable release
or a clean-machine installer. Once assets are present, no cloud account, API key,
cloud allowance or runtime download is used by this conversation engine.

Run checks with the host ThemHands venv Python and this directory's `check.py`.
`--recognition` runs the ten synthetic fixtures; `--voice-benchmark` sends paced
synthetic speech through the full local session without recording or playing.
`--benchmark` isolates typed-input model/TTS timing. These development commands
can load the model and use CPU/GPU resources. Model tools are stubbed out in the
benchmark; scope/argument rejection and routing are tested separately.

`Build-Window.ps1` compiles without launching. `Start-Streaming.cmd` is an optional
**user-invoked development pilot**, not the production launcher. Exit the working
app first to avoid competing speech/model workloads. A Talk click is required for
microphone access; mute disables the track; Stop talking releases it. Logs omit
PCM and transport credentials. The UI/window was not automatically launched.

Local evidence:

- `C:\SimplicityAI-Lab\StreamingPrototype\logs\voice-streaming-benchmark.json`
- `C:\SimplicityAI-Lab\StreamingPrototype\logs\recognition-check.json`
- `C:\SimplicityAI-Lab\StreamingPrototype\logs\stream-*.jsonl`

Nine automated checks cover segmentation, VAD timing, invalid target/arguments,
native tool routing without speaking JSON, stale events/cancellation and bounded
capture reset. Python compilation, JavaScript syntax and native compilation passed.
No repairs, host networking, security settings, VM configuration or BRS files changed.

Follow-up comparison and observed GPU restriction: see MODEL-RUNTIME-COMPARISON.md.
The working model remains unchanged; investigate the normal power/cooling mode
before drawing normal-speed conclusions.

Power-mode follow-up: the user-selected normal performance profile relieved the
observed restriction; identical Qwen text case6.19s->1.11s. A correct plain-language
synthetic voice answer had audio available4.83s. Still misses2–3s. Separate
Start-Voice-Pilot.cmd/desktop Voice Pilot shortcut selects Qwen8B only for a
live development test; normal installation/default20B unchanged. Read the newest
MODEL-RUNTIME-COMPARISON.md section before interpreting restricted results.

Live diagnostic pilot follow-up: spoken “Simplicity A I” failed the old exact
current-Windows name check, causing repeated questions despite two attempted tools.
TargetConversation now accepts narrow app-name speech variants in explicit
running-Windows wording, keeps original text/evidence unchanged, and retains the
confirmed target. Another/outside/negated target still revokes binding; a bare yes
never selects an unknown target. Exact first user transcript replay selected the
network tool and explained its synthetic result without a confirmation loop.
Nine checks pass. Exit/reopen Voice Pilot to load this scope fix; no new install.
Broader troubleshooting judgment remains under evaluation.

Browser/tool-awareness follow-up: the pilot now exposes get_tool_capabilities and
open_browser_window through its isolated ThemHands ToolState extension. The latter
opens standard-installed Microsoft Edge with --new-window about:blank, observes a
new visible window belonging to that exact executable, and attempts foreground
activation with normal Windows APIs. No arbitrary path, URL, shell command, keys,
page navigation, cookies/history reads or settings changes are exposed. Failure
to observe a new window is reported honestly; a launch request is not success.
This is not a web-loading/connectivity test or general desktop-control integration.

Browser launch outcomes use a grounded report from window evidence, not a freeform
network diagnosis. Early replay incorrectly called intentional blankness a failure;
that interpretation is now excluded from this report path. The model still chooses
the tool. Narrow ThemHands identity/install questions get authoritative connected-
capability facts, preserving action requests for model/tool execution. Activity
records label these app-generated reports. Synthetic results are explicitly marked.

The server job now permits explicit child breakaway only for the fixed external
browser launch. It does not enable silent breakaway; speech/collector guards remain
unchanged. A real Windows test using harmless sleeping processes verified server
Exit kills ordinary workers and preserves the explicit external child, which was
then cleaned up. This prevents assistant Exit from closing an external browser.
References: Microsoft Win32 Job Objects and SetForegroundWindow documentation.

18 checks pass across check.py and check_browser.py. They include executable/URL
argument rejection, another-PC/VM scope blocking, existing-window false-success
prevention, cancellation, foreground uncertainty, capability facts and worker
lifetime. Python compilation passes. Model replay selected the browser tool after
a contextual request. Browser launch/window observation itself has NOT been run
against a real browser yet: the user owns the next pilot. No app was restarted.
Exit/reopen Voice Pilot to load the new tool and launcher. Ask it to open a browser
in the Windows running SimplicityAI and report whether a window actually appears.
Local replay evidence is in StreamingPrototype/logs/browser-conversation-*.json.


## November 1: general ThemHands desktop pilot

Added isolated Windows-MCP stdio bridge, observed-control click/type/scroll/switch tools, fixed app/HTTPS launches, exclusive Desktop text creation with reread, and launcher/Lazesoft reference inventory. General input blocks terminal/admin/Lazesoft recovery processes. No validated clone/restore/erase/password workflows. Text-only Qwen has no visual interpretation of inaccessible controls. Desktop requests use current running Windows; another host is still not connected.

Read-only driver probe verified seven actual tools, protection enabled/balanced/1.5-second idle; real UIA snapshot returned 100 controls. 28 boundary/regression checks pass. Model routing checks are synthetic, not live desktop evidence. Initial Lazesoft model answer invented limitations; catalog is now injected automatically for relevant requests. Live user test is next: Exit/reopen Voice Pilot, open Google and inspect actual page, then create Simplicity Test.txt. No running pilot was restarted and no user desktop input was issued in these checks. See streaming/DESKTOP-CONTROL.md.


## November 1: complete authorized desktop tasks; keep voice enabled

User's real pilot opened Edge and eventually observed Google but never typed/submitted the requested search. Permission-only and future-action drafts are now withheld for desktop requests, with bounded continuation toward the whole task. Ordinary browser/search steps do not require repeated approval; this does not authorize destructive recovery work. Every successful app launch, switch and control input now forces a fresh observation before another decision or completion report. Requested searches require an observed search destination rather than just a launch or typed-input claim. New chat resets pending desktop work.

The exact noisy spoken Google/computer-speed-test request passes a simulated local-model replay: launch, observe, type, observe, submit, observe, report. Fixture was updated to reflect entered text and the actual Search button; initial one-field fixture was insufficient. 31 Python regression checks and client voice-handler checks pass. Four local-model routing cases pass using simulated desktop results; real live control still requires user retest.

No idle voice timer exists. Two overload paths were found: browser send backlog shut off capture; server recognition queue overflow closed the session. They now discard stale audio/reset recognition and resume without disabling voice, with explanatory status and recorded voice-state/transport events. No stop/error event in the inspected log established the precise trigger of the user's reported shutdown, so the cause remains unconfirmed. Spoken stop/cancel stops the reply while keeping listening; explicit stop listening turns voice off. WebSocket closure now retains a reconnect explanation instead of being overwritten by generic Voice off text.

User next: Exit/reopen Voice Pilot, ask it to open Google and search computer speed test in one request, then leave voice enabled and report any shutdown/status. No app restarted during development.


## November 1: Task Manager/CPU evidence and trustworthy conversation export

Live user test verified Google search launch + observed search results. Task Manager was absent from the fixed app catalog; model refused it. Added Task Manager launch and get_cpu_process_snapshot: ~1-second process CPU-time delta, normalized across logical processors, top ten sampled processes, inaccessible/exited/new-process limitations, no process termination or setting changes. Real read-only collector probe completed in 1.018 seconds and returned ten ranked rows. CPU measurements differ from Task Manager CPU Utility and are not a diagnosis.

ConversationLog.txt existed but contained only three recent user messages. Export now reads the app's full recorded transcript directly, both speakers, rather than asking the model to reconstruct it. Conversation/session document requests route directly to export_conversation, choose a unique filename by default, exclusively create and reread the file (4 MB bounded export), and report message count. Includes the export request, excludes its later confirmation; raw recognition and historical assistant claims are preserved. User's existing file left unchanged. Reconstructed 12 recorded messages from the real session event log into Desktop/ConversationLog-Verified-20261101-163947.txt; reread verified.

35 Python regression checks pass. Five simulated local-model routing cases pass, including the noisy Task Manager/CPU request selecting launch, observation and CPU sample and reporting the measured test process. No Task Manager GUI was launched during development. Current pilot not restarted. Next user test: Exit/reopen Voice Pilot, request Task Manager and highest CPU process, then export the conversation to a Desktop document.


## November 1: integrated troubleshooting baseline (not launcher integration)

User requested a broad common troubleshooting toolkit and agent/skill understanding, rather than adding one missing function after each random test. Added fixed inspect_windows categories: system, storage, devices, drivers, services, events, updates, security, startup. Added embedded symptom-to-tool skills and app-owned routing of explicit diagnostic requests/common symptom statements before prose. Data includes scope/time/available-or-unknown/bounds; collector-calculated storage units avoid raw-byte mental arithmetic. Read-only facts, diagnosis and future recommendations remain distinct. No additional model agents installed; one local model uses the tool layer and skill router.

Expanded fixed system-utility launch catalog with Device Manager, Disk Management, Event Viewer, Services, System Information, Reliability Monitor and Settings. Administrative MMC windows remain observation-only; CIM/native collectors read the underlying evidence. Added generic browser search primitive/workflow with encoded query and actual page observation; simpler reliable skill avoids permission-only multi-step stalls. Windows context excerpts preserve full local evidence logs and label omitted rows; older complete chat exchanges are retained within budget.

All nine collectors were exercised read-only. Native .NET event reader fixed a host Windows PowerShell Diagnostics module failure without changing execution policy. Secure Boot and current BCD status remained unknown due to unelevated access. No scans, repairs, driver install, device disabling, disk edits or process termination ran. Existing SFC verification/DISM recorded-health tools remain available with their original current-Windows/admin scope. Offline Windows, boot corruption diagnosis, full SMART/surface testing and destructive recovery workflows remain unvalidated.

47 Python regression checks and browser-client voice checks pass. Seven diagnostic local-model scenarios and five existing desktop/catalog scenarios use synthetic results and pass; not a certification of real-world diagnostic reasoning. Baseline references: streaming/TROUBLESHOOTING-BASELINE.md; host read-only probe evidence is in StreamingPrototype/logs/baseline-*.json (not Git). Normal app, BRS media, VM and user power mode unchanged; running Voice Pilot not restarted. Next user action: Exit/reopen Voice Pilot, describe a normal troubleshooting problem or request storage/device/driver/error assessment without changes.


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
