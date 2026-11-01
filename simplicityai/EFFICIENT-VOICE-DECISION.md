# Efficiency decision — November 1

Choose a CPU-first modular streaming architecture for ordinary Windows PCs:

- sherpa-onnx is the selected runtime to evaluate for streaming recognition.
- A speech-aware VAD such as Silero is the selected direction to replace simple
  energy detection; it is not installed or integrated by this decision.
- Keep the user's selected Kokoro voice, the 0.6.2 bounded opening-audio overlap,
  and existing ThemHands tool boundary.
- Keep current reasoning model until a smaller candidate passes tool/diagnostic
  behavior tests. Thread tuning has not provided a useful speed increase.

This is a modular speech pipeline, not a native speech-to-speech model. The
native models researched do not establish efficient operation on this 8 GB GPU,
let alone weaker CPU-only recovery machines. Do not download a larger native
model simply because it offers full-duplex conversation in its demo.

## Isolated Windows CPU experiment completed

Installed into C:/SimplicityAI-Lab/SpeechStreaming/deps only:
sherpa-onnx 2.0.1, sherpa-onnx-core 2.0.1, numpy 2.5.4; existing managed Python
3.12.16 executes it. No changes to existing Whisper/Kokoro environments.

Downloaded official English streaming Zipformer 20M model archive (127887156
bytes), extracting only named regular model/token files (45202074 bytes).
Source URLs and locally computed SHA256 are in SpeechStreaming/model-sources.json.
These hashes establish local file identity, not independent publisher attestation.
Weights/archive remain outside Git and outside the app/VM distribution. Licensing
review of the model assets remains required before redistribution.

Four existing clear synthetic Kokoro clips processed in 0.09–0.20 seconds each
on CPU versus the earlier Whisper benchmark around 2.7–3.1 seconds. However,
the recognizer dropped the beginning of all four phrases, losing key information
such as BitLocker and part of Calculator. An explicit boundary-padding experiment
did not resolve it; neither did a separate 16 kHz whole-input check on the first
clip. Cause is unresolved: do not call it inherent to the model or runtime.
No production promotion is justified from these results.

Evidence outside Git:
- logs/streaming-asr-benchmark.json (unpadded)
- logs/streaming-asr-padded-benchmark.json (1.5 s boundary padding experiment)
under C:/SimplicityAI-Lab/ThemHands.
Runner: prototype/benchmark_streaming_asr.py. Padding can be reproduced using
`--padding 1.5`; default reproduces the unpadded harness. The inputs are unpaced
100 ms chunks, so these are throughput tests, not live conversation timings.
No microphone, audible playback or Windows tools were used.

## State

Architecture selected; streaming recognizer not yet qualified or integrated.
Existing Whisper remains active. 0.6.2 host source is staged and still needs user
Exit/reopen and live verification. No app/model replacement, paid/cloud work,
VM update, microphone activation or general desktop changes were made here.

## Primary references

- https://k2-fsa.github.io/sherpa/onnx/ — local ONNX runtime and Windows support.
- https://k2-fsa.github.io/sherpa/onnx/pretrained_models/online-transducer/zipformer-transducer-models.html — small English model and official download.
- https://github.com/snakers4/silero-vad — speech-aware detection and CPU ONNX support.
- https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/minicpm_o4dot5_en.md — documented 12 GB NVIDIA full-duplex configuration.
- https://github.com/NVIDIA/personaplex — native duplex and CPU offload; no demonstrated speed on this host.
