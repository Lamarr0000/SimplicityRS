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
