# Host speech overlap — 0.6.2

Opening speech is now prepared privately while the streamed model reply finishes.
Only one bounded opening section is retained in memory. It cannot be retrieved
until the complete final reply passes the existing narrow advice checks and its
opening exactly matches the prepared text. These checks are not a semantic truth
verifier. Tool calls, rejected drafts, rewritten openings, new turns, Stop, mute
of output, reset and Exit discard speculative audio. No draft audio is played.

The client requests prefetch only when spoken output is enabled. Other replies,
short replies with no stable early boundary, and failed speculation use normal
speech synthesis. First section is at most 80 characters, later sections 160,
split at words/sentences. No extra voice controls were added. Speech synthesis
operations are serialized so cancellation cleanup cannot overwrite a new request.
A cancelled cache waiter raises a stop error rather than restarting stale audio.

## Measurements

Existing gpt-oss:20b, automatic model CPU allocation, existing Kokoro with two CPU
threads. No new model, cloud connection, microphone or audible playback used.
Synthetic warm model/text-to-ready-audio comparison with alternating pair order:

| Question | Sequential ready audio (s) | Overlap ready audio (s) |
| --- | --- | --- |
| Memory vs storage | 10.60 | 8.48 |
| Limits of a DNS timeout | 11.01 | 8.98 |

Raw: `C:/SimplicityAI-Lab/ThemHands/logs/speech-overlap-80-benchmark.json`.
Runner: `prototype/benchmark_speech_overlap.py`. Both modes use the same new
80-character opening. Timing begins at model request and ends at first WAV
availability, excluding transcription, UI polling, decoding and actual playback.
Model duration was 7.34–8.24 seconds. Prompt caching and wording differed in the
DNS pair; this tiny sample is directional evidence, not a guaranteed percentage.
An initial 120-character trial had a cold first model request and is retained in
`speech-overlap-benchmark.json`; do not use that cold comparison as a speedup claim.

Whisper greedy beam-size 1 vs existing beam-size 3 was also measured with four
clear synthetic Kokoro clips. Both recognized the meaning, including BitLocker
and Ethernet, but warm times were approximately 2.7–3.1 seconds in both modes.
No useful speedup justified changing production recognition. Real accents/noise
were not evaluated. Existing beam-size 3 and CPU threads 2 are retained.
Evidence: `asr-decode-benchmark.json`; synthetic fixtures stay outside Git.

## Limits / next test

This saves about two seconds in these warm text-to-audio examples. It does not
solve the full conversational delay. Model generation and per-utterance ASR
remain major waits; energy-only VAD can still mistake coughs for speech.
CPU-only operation on a weaker integrated-graphics PC remains unmeasured.
Do not promise ChatGPT voice latency or select a heavier model from these tests.

83 Python tests plus conversational and continuous-audio JS suites pass, including
late tool calls, draft rejection, cancellation of waiting playback, exact-match
approval, authenticated cached delivery and stale-worker cleanup. Host files are
staged with backups; manual Exit/reopen is required for live testing. The earlier
automatic review blocked scripted restart, so no launch workaround was attempted.
The VM installer remains 0.5.2 and must not be used for this host update.
