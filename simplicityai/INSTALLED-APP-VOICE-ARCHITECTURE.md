# Installed app inspection and offline adaptation — November 1

User requested inspection of this app's installation to identify an offline
adaptation for SimplicityAI, with Codex allowance efficiency a priority.
This was a read-only audit, not another live app update.

## What was actually inspected

Running desktop executable:
C:/Program Files/WindowsApps/OpenAI.Codex_26.1027.3384.0_x64__2p2nqsd0c76g0/app/ChatGPT.exe

The package is a Chromium-based desktop shell with resources/app.asar, native
helpers and separate Codex executables. Its ASAR directory has22423 files.
Read archive metadata and selected named static voice bundles directly. No archive
code was executed or transplanted. No app installation, authentication, account
profile, stored conversations or network settings were changed. No microphone or
audio playback was activated. Saved independent observations, not copied app code.

Inspection evidence outside Git:
C:/SimplicityAI-Lab/Diagnostics/AppArchitecture/
- asar-inventory.json
- voice-component-observations.json
- static-voice-events.json

## Confirmed client components

| Installed asset | Observation | Offline adaptation |
| --- | --- | --- |
| realtime-buffered-audio-worklet-a8e2ed28bf2f.js | Input buffering while connecting, pre-roll, bounded circular buffer, mute clears buffered input, release/replay/live phases | Own capture worklet and bounded input queue that preserves initial words while a local service starts |
| dictation-audio-worklet-7321ca3c5dd7.js and vad-audio-frame-processor-c51bdd028843.js | Audio processing off the UI thread, frame-oriented transfer | Feed a local online recognizer throughout speech instead of uploading a whole WAV afterward |
| silero-vad-6c9add9207e5.js | ONNX Runtime speech detection; static references to Silero V6 model and WASM resources; 16kHz/512-sample frames | Use separately obtained open-source Silero/ONNX components bundled for offline use; no dependency on the installed private bundle |
| voice-dsp-799d2dff5714.js | AudioContext, getUserMedia, echo-cancellation request, frame processor and VAD integration | One maintained audio path with speech detection and device/mute state |
| voice-session-646377aae369.js | Dedicated voice-session module; WebSocket, backend conversation, device and playback-blocked identifiers | Independent voice session and task state, rather than scattered conversation/playback booleans |
| realtime-controller-5c9cda7ea857.js | Session events and speech/task-related routing identifiers | Explicit lifecycle, text/audio events and scoped interruption handling |
| voice-prewarm-990a7aeed1d6.js | Prewarm component and RTCPeerConnection reference | Prepare owned local workers/model before the first question, with honest readiness status |

The buffered-audio worklet above concerns INPUT while connection is being
established. Do not misdescribe it as proof of a particular speaker playback
implementation. Identifier presence establishes component references, not that
every path is active on every account/device/session.

No .onnx/.gguf/.safetensors/.pt/.pth/.tflite model files were found in the examined
ASAR directory. Silero's static loader points to model/runtime resources on a
public static host; the large JSON asset inspected was animation data. This is
not an exhaustive search of caches/native binaries, nor proof that no model data
could ever exist elsewhere. We found no complete offline reasoning or native
speech-to-speech model to transplant from the examined installation.

## What public documentation adds

GPT-Live documentation describes a full-duplex spoken frontend with separate
delegated backend reasoning/tools. Applications own permissions, functions and
task progress; interruption need not cancel backend work. It requires an OpenAI
service connection and project key. This is evidence for a design pattern, not an
offline implementation or proof of the complete private ChatGPT server architecture.

https://developers.openai.com/api/docs/guides/live
https://developers.openai.com/api/docs/guides/live-migration

## Significant offline adaptation

Preserve the SimplicityAI window, tool adapter, selected voice and local assets.
Replace the conversation transport/controller as one bounded prototype:

1. Authenticated local audio/event transport sends short PCM frames continuously.
   A persistent online Zipformer stream decodes during the utterance and flushes
   at its endpoint. UI can show partial text without executing it as commands.
2. Speech-aware VAD replaces the current energy-only detector. Acquire public
   Silero assets independently, keep license/provenance, serve them locally.
3. A single session controller owns capture, turn IDs, input replacement, task
   delegation, playback queue, playback position, explicit cancellation and Exit.
   Keep conversation interruption distinct from cancelling a diagnostic task.
4. Forward useful text as model content arrives, and approved speech segments
   into an audio queue. Redesign the reporting gate around streamed segments;
   retain hard tool/target checks and never report an action before tool evidence.
   No internal reasoning/thinking tokens should be displayed or spoken.
5. Warm owned local workers/model and expose readiness. This moves cold loading
   before the first question; it does not erase loading cost or increase tokens/s.

Current gaps: capture uses an AudioWorklet but posts one completed WAV; fast ASR
still works per utterance; model text is buffered until completion; Kokoro returns
whole WAV sections; interruption discards rather than resumes playback position.
Thus this is a core session/streaming replacement, not a cosmetic app-window change.

## Decision gate to limit allowance spending

One end-to-end prototype, one measured comparison. Measure time from end of user
speech to first USEFUL spoken response, transcription accuracy including negation
and controls, interruption, task cancellation and CPU/memory use. Target roughly
2–3s for simple conversation on the host; diagnostic execution timed separately.
Do not count a canned acknowledgment as a useful response. No latency guarantee.

The measured model can still limit the result: one warm real-chat replay had
first content3.24s and full completion5.92s; other warm turns spent~10s generating.
Architecture alone cannot make that model's underlying computation disappear.
If the full prototype misses its target because of inference, make a model/runtime
decision from quality and speed tests, rather than continue unrelated small changes.

No offline-adaptation code was implemented during this audit. No new install,
restart or user test is needed for the inspection. Existing staged role/timing
hotfixes and earlier live0.6.3 state remain as previously documented.
