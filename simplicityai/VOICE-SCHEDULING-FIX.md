# Missing spoken reply — November 1

User reported slower-but-more-acceptable transcription/text and no voice after
reopening staged 0.6.2. Host evidence `logs/20261101-124402-5fe528.jsonl` shows
model response completed in 8.0 seconds, transcription calls 3.4/4.2 seconds, and
an assistant text event, but no client text-reply timing or Kokoro/audio request.
This points to the client scheduling path before synthesis, not a demonstrated
Kokoro generation failure. Logs do not by themselves establish what sound was
detected or whether it was noise, echo or user speech.

Reproduced client bug: `interrupt()` unconditionally set `autoNext=false` on an
energy-based onset, even when nothing was speaking and no replacement words were
recognized. That suppresses the pending reply's automatic readout. The new UI
regression test fails with false != true against the pre-fix HTML and passes with
the corrected HTML. Reproduction files remain outside Git at
C:/SimplicityAI-Lab/Diagnostics/voice-ui-regression-062.

## Fix

- On sound onset, stop playback/preparing playback promptly if already speaking.
- When awaiting an answer, preserve automatic speech and speculative preparation
  until a nonempty replacement transcript is received.
- A confirmed replacement transcript cancels the old task, then queues the new
  turn until the old task stops. Stop/cancel voice commands still end voice mode
  and now also request cancellation of a busy model turn.
- Existing explicit Stop, output mute and Exit behavior remains in place.

Both conversation UI and continuous-audio JS suites pass. Added checks verify
that an unconfirmed onset causes neither model stop nor speech stop, the pending
answer still requests/starts playback, and confirmed new words request old-task
cancellation. No microphone or audible playback was used by the developer.

Only HTML and the UI test changed; server remains 0.6.2. Host interface is backed
up and replaced; user Exit/reopen loads it. Earlier automatic review blocked
scripted restart, so no alternate launch was attempted. Live voice confirmation
is still required. Experimental streaming recognition remains unqualified and
inactive; Whisper/Kokoro/model settings are unchanged by this fix.
