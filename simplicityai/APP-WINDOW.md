# Dedicated SimplicityAI window — 0.5.0

The launcher owns a compiled WinForms/WebView2 window plus a local Python server.
The interface is local HTML; it opens without a browser tab or address bar. Existing
Start-ThemHands.cmd and the elevated helper both use launcher.py. No new voice or
model runtime is needed. Windows 11's WebView2 runtime and .NET Framework 4.8 are
required. The Microsoft SDK package provenance and hashes are in WINDOW-RUNTIME.json.
Build the native executable with prototype/Build-AppWindow.ps1 after placing the
three SDK runtime DLLs in the requested window-runtime directory. Generated binaries
are deployment artifacts excluded from Git; source, builder, manifest and installer
are tracked. Microsoft package licensing ships with the payload.

Closing the window (X or Alt+F4) returns to the owning launcher, which requests an
authenticated shutdown, waits up to five seconds, then terminates its exact server
if necessary. Windows kill-on-close jobs contain the server descendants and the
window's renderer descendants. The explicit Exit button also requests shutdown;
the window notices its service stopping and closes. A launcher crash closes its
owned jobs. No process-name-wide kill commands are used. Existing servers are never
taken over, and a second launch refuses to replace an active session. User-created
Calculator windows and pre-existing host Ollama/relay services are not terminated.
An in-progress verification collector can be terminated when the app exits; logs
may therefore contain a partial check. This is exit, not a successful completion.

The HTTP shutdown endpoint requires the existing session token, expected loopback
Host and same-origin restrictions. The native shell permits only its exact local
page, blocks pop-up windows and exposes no JavaScript-to-shell API.

The composer and app header stay anchored, with the conversation scrolling between
them. Keyboard focus, responsive widths, readable message spacing and compact
per-reply controls complement the existing auto-scroll and copy behavior. Activity/evidence, collected facts and connection/voice status are menu items under
the top-right Tools menu (three dots). They open focused panels with copy controls
instead of occupying the conversation. New
processes start a fresh conversation; refresh retains the current session.

Host verification: actual native window rendered successfully; Exit stopped its
service and closed the window; reopening was empty; Alt+F4 also stopped its service.
60 Python tests and conversational UI/audio/scroll checks passed. A real Windows
process-tree test verified owned descendants exit while an unrelated sibling stays
running. No microphone or
model inference was used for the window smoke tests. VM deployment and live voice
playback in the native window still need user verification. Text/speech latency and
foreground Calculator behavior are unchanged by this update.

## Voice controls — 0.5.1

Talk captures one message. Voice on/off toggles continued listening between
spoken replies, including retrying initial silence. Both modes pause recording
while processing or playing speech. Stop cancels capture/playback and requests
turn cancellation; turning voice off stops listening without cancelling an
already-running text turn. Sound remains a separate playback preference.
No barge-in or full-duplex speech is implemented.

After host reboot, the existing host Ollama and TLS relay must be started and
ready before guest chat can connect. A listening port alone did not establish
readiness during the roughly 58-second GPU initialization observed today.
Connection error text now names the services to check. Startup services are
still manual; no Windows startup settings were changed.

## Simplified voice and earlier playback — 0.5.2

Supersedes 0.5.1: one Talk button starts continuous conversation and becomes Stop
talking. Mute mic/Unmute mic pauses capture while Sound on/off controls reply
playback. Wait for Listening — speak now; Preparing means the device is not ready.
No microphone opens until Talk is selected.

Whisper capture now precedes recognizer loading. All initial captured blocks remain
in the in-memory recording. Transcribing is shown as a separate state. Kokoro stays
loaded while idle; active synthesis remains cancellable and Exit stops it. Speech
is divided into bounded sentence/word sections, allowing the first section to play
while the next is prepared. This is segmented playback of an approved complete
text reply, not native speech-to-speech or token-by-token model audio.

65 Python tests and UI checks pass. Host synthetic timings: 4.40 seconds cold and
1.59 seconds retained for roughly 3.4-second phrases. These do not establish guest
timing, fix every recognition error or add barge-in. No user audio captured during
development tests. Live guest onset/playback verification remains pending.
