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
