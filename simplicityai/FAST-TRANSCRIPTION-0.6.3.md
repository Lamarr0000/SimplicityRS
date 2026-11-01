# CPU transcription host pilot — 0.6.3

## Live host follow-up

User confirms quick transcription and simultaneous text/voice. Latest live ASR
roundtrip was0.41s with zipformer and zero queue delay. The first model request
took28.1s, including12.95s loading,5.73s prompt processing and9.37s generation.
The next warm request took12.5s, with first audio22ms after text (prefetch hit).
Thus the reported25–30s initial delay was substantially cold loading, while warm
reasoning/generation remains a noticeable delay. Later audio sections required
5.0/6.5/0.8s preparation; continuous-speech smoothness is not established.
Evidence: host logs20261101-130540-0405b7.jsonl and130708-458d58.jsonl.
Host pilot is now running/live confirmed, superseding staging notes below.

User confirmed the speech scheduling fix: voice works again, slightly faster.
The next requested work is faster transcription. No further user input was
needed for isolated synthetic testing.

## Selected host pilot

Use sherpa-onnx 2.0.1 with the int8 English streaming Zipformer 2023-06-26 model
(about 73.4 MB of model/token assets), CPU, two configured inference threads,
greedy decoding. Retain Whisper small.en as a lazy fallback for a single decoded
word outside a small fixed set of familiar acknowledgments/controls. For example,
the fast model heard synthetic "Cancel" as "counsel"; the fallback returned
"Cancel." correctly. No alias silently changes counsel into cancel. This narrow
heuristic does not detect every recognition error or establish general accuracy.

Kokoro voice and gpt-oss reasoning are unchanged. Voice tools retain the existing
target/argument checks. The speech-scheduling hotfix is included.

## Measured qualification

- The earlier 20M candidate dropped initial words and remains rejected.
- The larger candidate preserved initial words on the first four fixtures.
  An insufficient 0.3-second tail flush clipped some final words/short commands.
  With explicit 0.8-second numeric silence at each boundary, longer phrases,
  Ethernet, key/no-key statements and negations were preserved in ten clear
  synthetic Kokoro clips. This padding is processed rapidly, not slept in real time.
- Complete candidate worker, including IPC: longer phrases ~0.26–0.48 seconds;
  Stop talking ~0.21 seconds. Cancel used the cold lazy Whisper fallback, 4.36 s.
  This is a small single-speaker synthetic sample, not a noise/accent benchmark.
- Existing Whisper comparison on these fixtures was roughly 2.6–3.1 seconds.
- One second of generated silence and seeded low-amplitude noise both returned
  empty text. Real coughs/speaker echo were not tested.
- A real owned-process test observed three fallback descendants. Closing the
  recognizer's Windows job removed all observed children. No mic/playback used.
- 86 Python tests plus conversational and continuous-audio JS suites passed.

The application still uploads one bounded in-memory WAV after an utterance.
Although this backend uses a streaming model, live partial transcripts are NOT
connected yet. These processing times exclude speech duration, endpoint silence,
model generation, UI polling and spoken output. Do not promise subsecond total
conversation latency or that the reasoning-model delay has been fixed.

## Assets and ownership

Research/host assets: C:/SimplicityAI-Lab/SpeechStreaming. Runtime packages are
isolated in deps; wheels' SHA256 matched PyPI release metadata. Model downloads
are pinned to a Hugging Face repository revision. Source/provenance records:
streaming-asr-model-sources.json and streaming-asr-runtime-sources.json.
No trust_remote_code, cloud calls, microphone activation or model downloads occur
in the runtime worker. Windows managed Python 3.12.16 is reused from the existing
SpeechConversation folder; packaged layouts may include their own fixed runtime.

backend.json enables only {"schema":1,"backend":"zipformer20230626"}.
If absent, the existing Whisper path remains default. Unknown configuration fails
explicitly rather than executing another worker/backend. The parent owns the
worker and its lazy fallback descendants through its existing kill-on-close job;
bounded WAV validation, serialized requests, timeout and cancellation remain.

The parent logs the backend used for each transcription. Input audio remains
in memory; only synthetic fixture audio is saved in benchmark files outside Git.
Logs: hybrid-asr-worker-benchmark.json, hybrid-asr-nonspeech-check.json,
streaming-asr-expanded-flush-benchmark.json, whisper-short-control-benchmark.json
under C:/SimplicityAI-Lab/ThemHands/logs. Earlier failed comparisons are retained.

## Deployment / rollback

Host-only pilot: 0.6.3 source and the fixed backend marker are staged with prior
source backed up. User must Exit/reopen Start-ThemHands.cmd. Earlier automatic
approval review blocked scripted restart, so no launch workaround was attempted.
Live microphone accuracy/timing remains unverified. VM installer stays 0.5.2.
No BRS, networking, encryption, security or recovery disk settings changed.

To return to Whisper, stop the app, rename the fixed host backend.json marker to
an inactive filename and reopen. No model redownload or system setting needed.
The existing single Kokoro voice is retained; no new settings menus were added.
Model licensing needs review before redistribution; this local host pilot does
not distribute the model as a recovery product.
