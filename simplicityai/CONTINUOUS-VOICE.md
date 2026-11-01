# Continuous voice host prototype — 0.6.0

Develop and test on the host first. After the host trial succeeds, consolidate one
VM update. The VM remains necessary for final device-routing, permissions, audio,
deployment and recovery-environment checks. The current shared installer remains
0.5.2 until the host trial is reviewed. No new model has been downloaded.

## Implemented architecture

Selecting Talk explicitly opens WebView2 getUserMedia audio with echo cancellation,
noise suppression and automatic gain control requested. An AudioWorklet processes
microphone blocks off the UI thread. The microphone remains open during reasoning
and playback. It is not looped to the speakers. Stop talking, Exit, page unload or
capture failure stop the tracks. Mute disables input tracks and discards partial
audio; unmute resumes the session. Actual echo cancellation depends on the device
and audio engine; the applied setting is shown in Connection and voice status.

An adaptive energy detector uses sustained speech for interruption, keeps up to
half a second of pre-roll and ends a phrase after about 0.9 seconds of silence.
Capture is capped at about 25 seconds; capped text requires review before Send.
This is continuous capture/detection with utterance-based transcription. It is
not semantic VAD, partial live transcription or native speech-to-speech inference.
Speaker feedback/noise may cause false interruptions and needs live testing.

Speech onset immediately clears current playback/queued audio and requests backend
cancellation. The existing cancellation boundary prevents subsequent tool actions;
an already-running tool call may finish. A new message waits for the previous
model turn to stop. Only the newest transcript is eligible; interrupted/stopped/
muted session results are discarded. Completed spoken sections are tracked in an
interruption note; the heard fraction of the current section is explicitly unknown.
The full text remains visible. This is coarser than sample-accurate audio truncation.

WAV audio is sent only to the authenticated local loopback transcription endpoint.
Its size, format, channels, duration and payload completeness are validated before
decoding. The recognizer remains loaded in an owned, cancellable process using the
existing local Whisper small.en assets. Audio stays in memory and is not saved or
uploaded to a cloud speech service. Normal conversation/evidence logs retain text.
Exit kills the owned recognizer and other owned descendants. Idle recognition and
Kokoro workers may remain warm during an open app session.

## Model research

MiniCPM-o 4.5 documents simultaneous audio/video input and text/speech output. It is
a candidate for separate evaluation, not a verified replacement for recovery
reasoning or tool control on this host. Your Quadro has 8 GB VRAM; throughput and
memory for a full duplex deployment must be measured before changing the baseline.
Moshi's own FAQ states its current setup does not support 8 GB GPUs. A larger model
does not automatically improve latency. Keep gpt-oss, Kokoro and ThemHands in this
prototype to evaluate the interaction layer independently.

Primary references checked November 1, 2026:

- MiniCPM-o 4.5: https://github.com/OpenBMB/MiniCPM-o/blob/main/docs/minicpm_o4dot5_en.md
- Moshi FAQ: https://github.com/kyutai-labs/moshi/blob/main/FAQ.md
- AudioWorklet: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletNode
- Echo cancellation: https://developer.mozilla.org/en-US/docs/Web/API/MediaTrackConstraints/echoCancellation
- Interruption/truncation reference: https://developers.openai.com/api/docs/guides/realtime-conversations

These sources describe public capabilities and architectural patterns. They do not
establish the private implementation of the user's ChatGPT voice session.

## Verification and next live test

71 Python tests plus conversational/continuous-audio JS tests passed. Tests cover
bounded audio, authentication, retained workers, pre-roll, utterance limits,
muting, permission cancellation, interruption, queued newest messages, stale
transcript rejection, playback notes and process cleanup. No microphone was used
by developer tests. Generated Kokoro phrases were recognized as:

- “Good morning, my computer will not start.” — 2.66 seconds transcription.
- “Please stop speaking. I have a different question.” — 2.61 seconds transcription.

Recognizer warmup was 2.52 seconds. These are host synthetic measurements, not
end-to-end human microphone latency. The host app window rendered and /health
reported 0.6.0. Live permissions, first-word capture, speaker echo, interruption
latency, mute and exit still require the user's trial. The VM app should stay
closed during that trial to avoid duplicate sessions and model contention.
