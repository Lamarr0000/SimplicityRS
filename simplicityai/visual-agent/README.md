# Offline visual-agent experiment

Isolated UI-TARS-1.5-7B experiment; not integrated into the working application.
Assets and private test output live in `C:\SimplicityAI-Lab\VisualAgent`, outside Git.

## Architecture and decision gate

Screenshot -> local vision inference -> parsed action -> local driver -> new screenshot
-> independently verified outcome. Preserve speech/UI and structured Windows diagnostics.
Start with image-only grounding, then a bounded local test application, then real desktop
tasks. Do not call fixture success evidence of live Windows control or diagnostic reasoning.
No cloud inference, subscription tokens, telemetry, or hosted endpoint is required.

The official deployment guide recommends a cloud 48 GB GPU configuration. That is not
a minimum for quantized inference and is not suitable to copy onto this 8 GB machine.
The experimental alternative is llama.cpp CUDA 12.4 with community Q4_K_M weights
(4,683,073,856 bytes) and the f16 vision projector (1,354,162,880 bytes). Weight sizes
exclude runtime buffers, image tokens and KV cache; fit and latency must be measured.
Community quantization is not an official ByteDance release or a validated equivalent.

## Sources

- Model: https://huggingface.co/ByteDance-Seed/UI-TARS-1.5-7B
- Official implementation: https://github.com/bytedance/UI-TARS
- Official deployment: https://github.com/bytedance/UI-TARS/blob/main/README_deploy.md
- Official coordinate guidance: https://github.com/bytedance/UI-TARS/blob/main/README_coordinates.md
- Agent/prompt reference linked by upstream: https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/uitars_agent.py
- Runtime: https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md
- Community conversion: https://huggingface.co/mradermacher/UI-TARS-1.5-7B-GGUF

## Initial scope

`probe.py` renders three differently positioned buttons and sends only pixels and the
requested button label to the local server. Coordinates are parsed with literal AST
validation, never eval/exec. Nothing is clicked on the real desktop. Reports contain
response latency, model output, parsed coordinates and bounding-box correctness.
The server URL is fixed to loopback; no API key is used. This is the first gate, not
the complete agent. Next gates: multistep screenshot feedback, recovery from changed
layouts, real Windows control, stop behavior, and repeat with external networking unavailable.

`feedback_probe.py` now exercises screenshot feedback, a simulated missed click,
target movement and independently checked completion. See RESULTS.md for measured
results and limits. Run probes using the existing ThemHands venv Python (Pillow).

## Native Windows lab

Run `Start-Visual-Agent-Lab.cmd`, or the desktop shortcut **SimplicityAI Visual
Agent Lab**. Wait for Ready; choose Drive report, Device details or Network report;
click Start visual test and keep the window visible. Stop or Esc prevents further
input; a pending inference can finish before another test becomes available.
Exit closes this app and its owned model server. It does not stop Ollama or the
working SimplicityAI installation. Do not run two GPU models during comparisons.

This is a real Tk Windows window with sample diagnostic screens, not a PC health
assessment. The model sees only a cropped screen capture, chooses coordinates,
and Windows-MCP sends actual Windows mouse input. Navigation changes the real UI;
completion is checked against application state. It cannot click outside its test
canvas, type, open other applications, or repair anything. Native foreground,
window geometry, screen bounds, occlusion sample points, revision and destination
checks reject stale/covered targets. This prototype is not a hardened general
desktop driver: foreground/occlusion can change in the interval before input.

Loopback model requests use a per-launch random bearer credential, inherited only
by the owned model process; no cloud account/token is involved. Runtime logs and
bounded-canvas captures stay under the external VisualAgent folder, outside Git.

## General desktop preview (experimental)

`Start-Desktop-Preview.cmd` starts a separate native task controller. It has primary
desktop screenshots rather than sample-area restrictions, and accepts literal click,
double/right click, focused text entry, shortcuts, scrolling and drag actions. The
existing local Windows-MCP driver executes them. Its default tool set remains
unchanged for the working app; only this preview opts into the additional Move tool.

The controller minimizes and activates the eligible application behind it using
normal Windows foreground APIs. If focus cannot be established, no task starts.
It retains the last two screenshot turns, actual assistant action history, and tool
failure feedback. Invalid model actions are not executed. Foreground changes,
expired screenshots, user takeover and protected targets stop the run. A repeated
action loop, 24-step limit and four-minute deadline bound execution. Text input
requires an observed focused editable, non-password control. Windows permissions
and UAC are not bypassed. Terminals, authentication/security targets and Codex are
not automation targets. No arbitrary model-authored shell/code is executed.

**Validation remains limited.** In a live Notepad test the local agent focused the
blank document and typed `Offline visual control test`; the developer independently
verified the visible text. The agent then proposed an unrequested close action,
which was blocked. An earlier Task Manager navigation test did not pass. Early
runs also exposed foreground-handoff bugs that were corrected; those runs cannot
serve as clean model comparisons. This preview is not a general-autonomy pass or
a replacement for the main SimplicityAI installation. It is not speech-connected.

Arbitrary task completion is a model claim, clearly labeled unverified by the app;
there is no universal independent verifier. The preview's desktop input boundary
has race limitations and is not a hardened sandbox. Windows application testing,
task adherence and final-action verification need further work before integration.

## Native context and administrator input checkpoint

The prompt now follows UI-TARS Desktop's `getSystemPromptV1_5`: persistent system
role, native `finished()`/`call_user()`, real action turns and the latest two images.
The active user task and actual tool result accompany each current observation.
Foreground-window captures include an explicit physical origin and resize transform;
this reduces confusion with background application caption buttons. Supported app
launches reuse the main app's existing catalog. A leading explicit open/launch/start
request is routed by the app, not claimed as model-selected reasoning.

Completed/blank Notepad replay checks passed four cases without sending UI input.
A live blank-document run typed the requested text and stopped with `finished()`.
Task Manager tests exposed an additional Windows input-integrity problem: the input
runtime was medium integrity (`0x2000`), while Task Manager was high (`0x3000`), both
without UIAccess. Windows UIPI blocks that input. An injection request is not proof
that the target received it. The new token preflight rejects this case before model
actions, rather than reporting repeated successful clicks. Unknown token access
also prevents input. Semantic action signatures now bound repeated-action loops.

**SimplicityAI Desktop Preview (Admin)** is a separate user-invoked launcher. It
uses normal Windows `runas`/UAC and changes no UAC settings. For this experiment it
elevates the whole preview, including child input/model processes. The user must
approve UAC. A production build should separate the privileged input broker from
the reasoning process. Administrator trials have since run; the latest reported completion was not independently verified. See the session checkpoint.

References:
- https://github.com/bytedance/UI-TARS-desktop/blob/main/apps/ui-tars/src/main/agent/prompts.ts
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput


## Independent acceptance outcomes — November 2

The preview now offers Custom task, `notepad-text`, and
`task-manager-performance` in a selector. Selecting a case fills its exact task;
editing that task disables its verifier. The existing Admin shortcut selects the
Task Manager case through `--acceptance-case task-manager-performance`.

At model completion, a separate read-only UI Automation traversal checks the
same foreground HWND/process identity before and after collection. Notepad
requires the exact test sentence in a visible editable document. Task Manager
requires a selected Performance item and visible CPU and Memory labels. Missing,
unsupported, incomplete or changed-window evidence remains unverified. Custom
tasks remain model claims. No model is asked to grade its own answer.

Collection is limited to 400 controls, depth 16 and a three-second cooperative
budget. Individual Windows accessibility calls can exceed that budget. Checks
currently expect English control names. They verify the final outcome only:
they do not prove no other tab was touched or no setting was changed earlier.
The evidence log records the predicate result and control count, not document
contents. Live accessibility compatibility and selector layout are pending.

Small live acceptance set (user-started, one model at a time):
1. Open the existing Admin preview shortcut, approve normal UAC, wait Ready,
   leave `task-manager-performance` selected, then Start task and Copy evidence.
2. For `notepad-text`, first open a new blank Notepad tab yourself. Select the
   case and Start task. Leave that test tab unsaved; do not use a personal document.
3. Repeat either case and press Stop/Esc while the model is thinking. Evidence
   must show cancellation without later input or a verified completion.

No live case was run for this November 2 implementation. Twenty automated tests,
Python compilation and administrator-launcher syntax validation pass. Explicit
catalog launches now proceed directly to launch/foreground observation rather
than depending on an unrelated window behind the controller. This does not add
freeform browser launch routing, universal task verification or voice integration.


## Bound Notepad test and early outcome stop — November 2

The Notepad acceptance case now requires a blank, selected English `Untitled`
tab. Before inference, it binds the window/process creation identity, selected
UIA tab runtime ID and document runtime ID. Named files, existing text, multiple
visible documents, missing identities and incomplete observations stop without
input. The original `New Text Document.txt` trial verified text but did not meet
this stricter document requirement.

Before each Notepad input the binding is checked again. Only the exact test text,
ordinary clicks inside the bound editor and wait/finish/help are allowed. Tab,
window, launch and keyboard shortcut actions stop the acceptance run. Typing
requires a focused point inside that same editor, an empty document and no submit.
A title auto-renamed by Notepad after typing is allowed if the runtime IDs remain
unchanged. Unknown/unexpected content stops without attempting cleanup.

Both acceptance cases check the fresh outcome before another inference. On a
pass the application stops and logs `completion_source: application verifier`;
it does not wait for a model completion claim or allow extra model cleanup. This
is controller behavior for explicit cases, not proof of improved model reasoning
or general task adherence. Custom tasks retain existing behavior. Snapshot/input
races remain; this is not a hardened sandbox. No automatic save/undo/close occurs.

24 tests and compilation pass. A real read-only Notepad UIA probe found one
visible document and one selected tab with runtime IDs (92 controls, complete).
No input or new live agent test ran during this change. Next live test: Exit the
preview, reopen it, choose `notepad-text`, open a new blank Untitled Notepad tab,
then Start task. Expect document_bound, typing, and application-verifier completion
without an extra model turn. Existing named documents should be rejected, not edited.
