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
