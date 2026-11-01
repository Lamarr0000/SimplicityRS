# Balanced local performance — November 1

The user clarified that changing models was an idea, not a request to switch.
Technical direction remains our responsibility: optimize for ordinary CPU-based
PCs, with GPU acceleration where available. No cloud migration is authorized by
that discussion. Do not replace the model just to make it larger.

## Measured host thread comparison

`prototype/benchmark_balance.py` runs sequential synthetic text requests against
the existing local gpt-oss:20b, same 8192 context and low reasoning setting. No
tools, microphone, diagnostic collection or model download. Each setting has a
separate warmup followed by the same two short questions. Raw evidence:
`C:/SimplicityAI-Lab/ThemHands/logs/balanced-thread-benchmark.json`.

| Model CPU threads | Warm first text, two questions (s) | Generated tokens/s |
| --- | --- | --- |
| Automatic | 3.62 / 3.61 | 8.58 / 8.65 |
| 4 | 3.79 / 3.61 | 8.32 / 8.43 |
| 8 | 3.67 / 3.73 | 8.68 / 8.53 |

Changing thread settings incurred about 16 seconds model load time in the warmup.
There is no useful improvement here to justify pinning a new thread count.
Automatic configuration is retained. The runner restores default options after
the comparison. These are two questions per setting in fixed order, not a robust
statistical comparison, concurrent voice workload, CPU-only test or tool-quality
evaluation. No claim of end-to-end improvement follows from these numbers.

Recent real client timing already showed approximately 3–5 seconds transcription,
7–13 seconds text reply wait and around 4 seconds first audio preparation, with
zero model queue wait in those turns. ASR and Kokoro each currently use two CPU
threads. The model is partly GPU-resident; a large memory allocation alone does
not prove which hardware subsystem is limiting it.

## Engineering direction

1. Keep existing model and tool behavior while isolating improvements. Avoid
   simultaneously loading multiple competing reasoning models.
2. Optimize the sequential speech handoffs. Evaluate preparing bounded speech
   sections as text arrives, retaining withheld output until its applicable
   reporting checks pass. Do not publish rejected drafts or claim tool results
   before successful evidence. Benchmark overlap because CPU contention could
   erase the gain.
3. Compare ASR decoding settings using fixed synthetic audio and accuracy checks;
   do not trade away first words or troubleshooting terminology for speed.
4. Replace energy-only speech detection with a speech-aware detector if validated
   locally. Coughs have been transcribed as messages; interruption must distinguish
   pausing playback from intentionally cancelling a diagnostic.
5. Measure a CPU-only baseline separately before promising performance on PCs
   with integrated graphics. Select a smaller default model only if it passes
   troubleshooting, uncertainty and tool-target checks. Larger is not the target.

These pipeline changes are next work, not implemented by this benchmark. No host
application replacement or restart is required for the comparison. Existing
0.6.1 source, logs, BRS and VM deployment are preserved.
