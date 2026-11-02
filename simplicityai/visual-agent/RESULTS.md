# First offline visual-agent gate — November 1, 2026

Installed isolated UI-TARS-1.5-7B Q4_K_M + f16 vision projector and llama.cpp
b12032 CUDA 12.4 under `C:\SimplicityAI-Lab\VisualAgent`. All model hashes
matched Hugging Face LFS SHA256; runtime archives matched GitHub release digests.
No modifications to the working app, speech stack, Windows settings or VM.

## Measured

- Host GPU: Quadro RTX 4000, 8192 MiB. Initially no compute model resident.
- Loaded vision model: approximately 6311 MiB GPU memory; 6583 MiB after tests.
- First cold image request: 53.823 seconds. Warm performance must not hide this.
- Final grounding fixture: Network left 2.432 s, Storage middle 2.101 s,
  Devices right 2.099 s. All predicted coordinates were inside the target bounds.
- Feedback fixture: Storage 2.373 s; injected missed click + target moved;
  corrected Storage location 2.093 s; report 2.112 s; finished 1.776 s.
  Independent simulator state confirmed the report was visible before completion.
- Parser boundary tests reject executable expressions, multiple actions, nonliteral
  arguments and coordinates outside the screenshot. No eval/exec is used.

## Important corrections and limits

Initial adapter mistakenly treated coordinates as normalized 0–1000, following an
older agent convention. UI-TARS 1.5's own coordinate guide uses resized-image pixel
coordinates. Corrected against that guide. Initial probe also placed all requested
targets centrally; final test uses left/middle/right and feedback includes movement.
Initial outputs are retained locally rather than discarded.

Final fixture images are 1120x784 (multiples of 28; >=1024 image tokens), so the
pixel space remains explicit. The launcher now also requests a 1024-token minimum
as recommended by the runtime. Arbitrary screen sizes/DPI mapping still need testing.

These are generated screenshot fixtures, not real Windows input. This proves local
image inference, initial grounding, screenshot feedback and a simple recovery case.
It does not establish general desktop reliability, diagnostic reasoning, speech
integration, cancellation, or performance on machines without a dedicated GPU.

Inference requests went only to loopback with local model/projector paths. No cloud
model/authentication was used. External networking was not physically disabled;
a disconnected end-to-end deployment test remains outstanding.

## Next gate

Use a bounded real test window for unfamiliar multistep tasks, screenshots after
each action, foreground/DPI identity checks, cancellation and verified completion.
Only then connect the visual agent to the existing ThemHands tools and speech UI.
Do not replace the current Qwen pilot solely because these fixture tests passed.

Local evidence: `grounding-results.json`, `feedback-results.json`, generated PNGs,
initial mismatch results and runtime logs under `C:\SimplicityAI-Lab\VisualAgent`.
Test server is stopped at this checkpoint to free GPU memory.

## Native Windows lab follow-up

Built a separate Tk Windows app and connected real screen captures to UI-TARS and
the existing local Windows-MCP input driver. App controls are canvas-rendered, so
the model receives pixels, not labels, DOM, accessibility coordinates or hidden state.
Application state is used only for independent completion checks.

Live results on the host at 250% scaling:

- Drive report: two real Windows clicks and verified finish, decisions 2.358,
  2.191 and 1.850 seconds.
- Device details: reached and independently verified the requested details, but
  required eight clicks plus finish (nine decisions, roughly 1.9–2.5 s each).
  Repeated/backtracking clicks are a reliability concern, not a clean efficiency pass.
- Network report: two real clicks and verified finish, decisions 2.463,
  2.180 and 1.868 seconds.
- Stop clicked during a pending response: saved cancellation and discarded the
  pending result after two already completed clicks. It did not report completion
  or send additional input afterward. Stop does not undo already completed input.
- Exit closed the owned model server, removed the loopback listener and freed GPU
  allocation. The regular SimplicityAI installation was not restarted or edited.

The first live attempt rejected the model's action formatting before sending input.
The adapter now accepts a single literal click with or without the Action prefix;
multiple actions and executable expressions remain rejected. Raw action output is
saved before parsing, including on later failure.

Parser and window-boundary tests pass. They cover cancellation, foreground change,
changed revision, covered destination, out-of-area points and coordinate mapping.
These unit checks are distinct from live tests; foreground/occlusion race hardening
and real non-lab application control remain outstanding.

User entry point: desktop shortcut **SimplicityAI Visual Agent Lab**. The lab is
closed at handoff; opening the shortcut starts its own local model. Keep it visible
while a test runs. All displayed diagnostic values are sample data. It is not yet
connected to speech or general conversation, and cannot act outside its test area.

## User timing investigation

Latest user run `windows-lab-20261101-201419-1.json` completed correctly but model
requests took 19.935, 21.223 and 20.590 seconds. Server timing attributes roughly
19.5–20.7 seconds to prompt/image processing; output generation was only 0.09–0.42 s.
This is a real slowdown versus the earlier isolated test, not established driver delay.

Read-only Ollama inspection afterward reported qwen3:8b loaded with size_vram
6,194,766,806 bytes. Alongside the visual model's measured ~6.6 GB, reported demand
exceeds this 8 GB GPU. Memory contention/paging is a leading hypothesis; a controlled
isolated rerun is still needed. Current Windows GPU usage alone cannot reconstruct
historical physical residency.

Added read-only startup preflight rejecting a resident Ollama model >1 GiB, plus
separate driver startup, capture, model, driver-call and elapsed timings. This check
does not detect every runtime or prevent another application loading a model later.
The input-driver duration includes its handoff/click path, not a separate measurement
of every release-indicator transition. No driver policy or user takeover was removed.

The attempted Qwen unload + isolated-test command was rejected by automatic policy
review. It was not retried by another route, and the isolated rerun remains pending.

## User isolated rerun and general-desktop preview

User provided a successful isolated Drive report run: driver startup 3.238 s;
screenshots 0.119–0.129 s; model calls 2.227, 2.095, 1.753 s; driver calls 0.975,
0.570 s; total 12.208 s with completion verified. This strongly supports competing
model memory demand as the cause of the previous large inference slowdown. The
separate claimed release-indicator delay was not measured in these records.

Added an experimental primary-desktop controller, native UI-TARS action parser,
real per-turn screenshot history (latest two images), literal action history and
recoverable tool feedback. Existing working app and its default tool scope remain
unchanged. Early live runs exposed controller foreground/minimization errors; these
were corrected with fresh HWND binding, deferred normal target activation, and
refusal to capture the controller. Those early runs are not clean planning evidence.

Final live Notepad run (local `desktop-preview-20261101-*.json`):
the agent clicked the Untitled tab, clicked the document body, and typed
`Offline visual control test`. Model decisions 3.798, 3.437, 5.641 s; driver calls
1.053, 0.583, 0.739 s. Independent Computer Use screenshot inspection verified the
exact text in the new unsaved tab (27 characters). Existing tabs/files were not edited.
It then proposed closing a window contrary to the task; the destination was protected
and blocked. Therefore text-entry capability passed, but full-task adherence did not.
Do not promote this as a reliable autonomous desktop agent or integrate it broadly.

The blank-test document remains unsaved as visible evidence. No save, close,
process termination, security change or recovery operation was performed by this test.

## Native-context completion correction and Task Manager permission diagnosis

Read the official Desktop `getSystemPromptV1_5`, not just the current Doubao prompt.
Adapted its persistent system role/native completion actions. Added bounded context
tests, current-task reminders, actual tool feedback and a no-input replay runner.

Four real screenshot replays (two completed, two blank states) selected correct
completion/noncompletion actions in 3.486, 3.309, 2.846 and 3.469 seconds. No input
driver is imported by that replay. Images remain local outside Git.

A subsequent live blank Notepad run typed the expected 27 characters and then
returned `finished()` with no save or close attempt. Model calls 4.166 and 5.650 s;
text-driver call 1.258 s. Independent Computer Use screenshot verified the text.
This corrects the previously demonstrated completion failure for this task only.

Further Task Manager runs failed. One model-only launch run rejected unsupported
shortcuts, then the model typed `taskmgr` into the unsaved test document and closed
Notepad. No disk file was saved. The test tab remains in Notepad's retained session;
original user file tabs were not edited. Do not hide this failure.

Explicit launcher routing subsequently opened Task Manager through the existing
catalog. Model clicks/Alt+Tab requests reported execution, but the visible interface
did not change. Read-only token inspection found a concrete mismatch: representative
input runtime medium integrity RID 8192/0x2000, Task Manager PID 25220 high integrity
RID 12288/0x3000, neither with UIAccess. Standard child input workers inherit the
preview's token. Microsoft documents UIPI preventing lower-to-higher input injection.
Inspection of the exact product-captured frame also showed that `(40,226)` was near
the actual Performance icon. Thus the repeated unchanged screen cannot be attributed
solely to model grounding/planning. Other incorrect model choices remain observed.

Added token input preflight (live test correctly rejects the medium-to-high case),
an explicit user-approved administrator launcher, semantic repeated-action detection,
and a three-invalid-action stop. No UAC approval, token modification or security
setting change was automated. Administrator retest remains pending user approval.
Preview/server closed; Task Manager remains open. Do not claim its Performance task
passed. Next required action is the Admin shortcut and normal Windows UAC approval.


## November 2: consolidated suite executed; CPU confirmed, Calculator planning failed
User requested less repeated cut/paste and explicitly authorized preview launch;
also offered manual UAC approval. Computer Use skill read and used for preview
lifecycle/independent screenshots. Medium helper could not control administrator
preview. User approved UAC and later closed the elevated previews when requested.
No UAC/security dialog automated and no security settings changed.

Implemented Run acceptance suite, --batch/--suite-cases and separate
Start-Acceptance-Suite-Admin.vbs. Sequential Performance/CPU/Calculator runs save
acceptance-suite-*.json summaries, full per-case logs and last model screenshot.
Stop/user takeover ends remaining suite cases; other failures are recorded and
next cases run. Notepad excluded by default to preserve user documents. Preview
height increased to show status. 31 tests and compilation pass.

CPU independent check now accepts selected Performance + CPU heading + >=3 of5
CPU-detail labels; optional CPU selection state recorded, not required. Insufficient
matching evidence is partially_verified, missing evidence unverified. Saved real
CPU screenshot independently inspected and visibly confirms CPU utilization,
speed, processes, threads, handles. Earlier strict selection flag was false despite
the correct screen. This is alternative independent evidence, not model self-grading.

Consolidated elevated report acceptance-suite-20261102-103226.json:
- Performance verified, one real click, model4.537s.
- CPU page verified immediately, five labels+heading; zero additional actions
  because prior case left CPU selected. Do NOT call separate deeper navigation pass.
- Calculator initially blocked by foreground identification; no input then.

Fixed actual compatibility causes before isolated Calculator rerun: top-level
ApplicationFrameHost owns Calculator on this build. Resolve only one actual
Calculator child process, preserve host_pid, check actual child's input integrity.
Normal foreground recovery requests newest observed matching app without bypass.
Calculator's observed UIA Header is Standard Calculator mode; accept that label.
Read-only real UIA probe:89 controls, complete, actual arithmetic button IDs/rects.

Final Calculator report acceptance-suite-20261102-103759.json:24 real model-chosen
button clicks,160.079s inference, then step limit. Repeated1/3/clear loop; no137+29=
or166. Independent final Computer Use screenshot visibly0. Launch/input capability
passed; arithmetic/planning failed. No structured Calculator fast path substituted.
No more user copying needed; evidence read directly from disk. Full consolidated
report C:/SimplicityAI-Lab/VisualAgent/consolidated-acceptance-20261102.md + .json.
Preserve earlier failures/evidence. _wmi signing issue remains separate/unresolved.

Preview Exit used to stop owned service after testing; verify final listener/GPU
state if resuming. Main Voice Pilot/normal app/VM/BRS not modified. Test Calculator
and Task Manager windows left; no user files saved/deleted. Next priority is model/
harness loop detection and planning/state reliability, varied cases before voice
integration; not more Task Manager prompt patches. No further live test this turn.
