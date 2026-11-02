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
