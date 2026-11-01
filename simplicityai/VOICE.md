# Voice and conversational interface

The current application uses one fixed Kokoro playback voice (af_heart). There is no voice selector and no Windows-voice or cloud-voice fallback. Microphone input remains the working installed Windows System.Speech recognizer. The user confirmed accurate dictation and audible Windows playback before requesting a more natural fixed voice.

## Simple main screen

The main interaction is a message box with Speak and Send. Sending a description prepares a proposed next step; it never starts a diagnostic. Simple follow-up buttons ask for the affected Windows environment or a supported problem category only when needed. A separate Run this check action is required. Advanced tools, measured facts and timestamped evidence are collapsed. Copy controls remain available in their respective panels. Progress and Stop remain visible during a task.

This is a conversational layout over bounded workflows, not a general chatbot or a validated autonomous diagnostic agent. Problem routing uses explicit keyword hints and asks when it cannot route. Another Windows installation or nonbooting Windows remains unsupported, with checks blocked rather than redirected to the running recovery environment.

## Playback

kokoro_worker.py runs the standard Kokoro v1.0 ONNX model on CPUExecutionProvider with two intra-op threads and one inter-op thread. The smaller int8 model was substantially slower on this host and is not shipped in the guest package. The runtime is isolated Python 3.12.16 with pinned packages in kokoro-requirements.txt. Model sources, sizes and SHA-256 hashes are recorded in kokoro-model-sources.json. Large runtime/dependency/model assets remain outside Git.

KokoroSpeech owns one warm worker. Text is JSON on stdin, never a shell command. Audio is transferred in memory and returned through an authenticated loopback endpoint as WAV. It is not uploaded or saved by normal playback. Requests are serialized, limited to two thousand characters and ninety seconds, with explicit Stop. Windows job-object cleanup closes the child if the server exits. Page departure requests cancellation. Starting microphone input or a diagnostic stops playback preparation. No GPU provider or cloud synthesis fallback is used.

Read aloud is opt-in. Stop speaking cancels both preparation and browser audio. The voice is a Kokoro preset, not the ChatGPT Sol voice.

## Microphone

Speak opens the default Windows microphone only after a click. A phrase is placed into an editable review box. Use these words adds it to the issue description, without starting a check, selecting a drive or authorizing a repair. Capture is bounded to forty seconds; only the owned microphone subprocess can be stopped. Check microphone support probes engine availability without activating audio capture.

Requires working microphone/speaker drivers, permissions, installed speech language and VMware audio routing. Nothing changes those settings automatically. If capture or playback fails, typing and on-screen replies remain usable. Submitted descriptions use the existing local task logs; raw microphone audio is not saved.

## Validation and limitations

Host: forty-one Python tests cover boundaries, fixed tools, capture cancellation, session authentication, WAV endpoint, text limits and persistent worker ownership. JS checks cover unique controls, progressive target questions, no automatic diagnostic start, reviewed speech text, Copy isolation and fixed playback/Stop. The voice engine probe and real Windows child-process cleanup were verified without capturing host microphone audio.

Standard-model CPU benchmark: 4.33 seconds of speech generated in 5.47 seconds on first request and 3.56 seconds on the next. A relocated package generated 3.89 seconds of audio in 6.83 seconds. These are small host samples, not guaranteed guest performance. Quantized-model samples took roughly thirty to fifty-five seconds and were rejected. The package is about 545 MiB.

Guest checks pending: new screen appearance, fixed Kokoro audition, playback responsiveness, and disconnected-network validation. No new system scan is needed to test this update.

## Deployment

Use shared-folder Install-Chat-Voice-Update.cmd after stopping the idle server. It verifies model hashes, saves previous source files and installs the local playback assets. Restart normally with Start-ThemHands.cmd and refresh the browser. Earlier installers should not be used to downgrade this version.

## Sources

- https://github.com/thewh1teagle/kokoro-onnx
- https://huggingface.co/hexgrad/Kokoro-82M
- https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine.recognize?view=netframework-4.8

Third-party runtime/package licenses are retained in the local asset bundle. Kokoro model and wrapper licenses are also retained alongside model provenance. No audio or model weights are committed.
