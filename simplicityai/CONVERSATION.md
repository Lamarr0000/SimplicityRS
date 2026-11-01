# Conversational voice prototype

This replaces guided forms and keyword routing in the main UI with a conversation
driven by the existing local gpt-oss model. No problem or target menus are shown.
The assistant can ask follow-up questions and choose supported read-only tools.
The interface does not establish ChatGPT-equivalent model quality.

## Voice session

Talk is explicit opt-in. Local Whisper small.en captures a short phrase, closes the
microphone, transcribes on CPU and submits the visible words as a chat message.
Kokoro reads the completed assistant reply automatically. When the reply finishes,
a Talk session listens for the next answer. Stop ends capture/playback and requests
cancellation of an active model turn. Silence, capture errors or playback failures
end the voice session; typing remains available. Captures reaching the time limit
are put in the message box for review and manual Send instead of auto-submission.

Normal speech capture stays in memory and is not uploaded or saved. Speech requires
working VM microphone/speaker drivers and permissions. This build uses English
Whisper small.en, CPU int8 with two threads, not the previous Windows dictation
engine. Whisper and Kokoro do not run concurrently with an active chat turn.

Browser playback now resumes a Web Audio context during Talk/Send/Read user gestures,
before asynchronous work. PCM WAV is decoded into that context rather than starting
a newly created audio element after a long request. Late replies after Stop are
discarded. Playback errors are shown, and worker initialization errors appear in the
local activity evidence. Browser autoplay behavior and the guest audio path still
need a live user test; the prior silence cause was not conclusively established.

Check-Conversation.cmd is an opt-in diagnostic. It generates a fixed synthetic WAV
under logs and probes engine/device availability without microphone recording. Its
report and WAV can distinguish generation failure from browser/speaker problems.

## Conversation and tools

Original issue and recent complete turns are supplied to gpt-oss. Transcripts and
recent model/tool context are saved in logs/chat-state.json across restarts. The
model context is bounded to recent turns plus the original issue; older visible
messages are not all guaranteed to be in the model context. New chat resets active
conversation state; per-turn diagnostic logs remain.

Restoring chat history never restores permission to inspect a Windows target.
Explicit phrases identifying the running Windows/this VM bind the target. Ambiguous
or host/other-installation requests do not authorize current-Windows checks. Supported
chat tools are health snapshot, network snapshot and requested long SFC verification/
DISM recorded-health check. No shell, repair, drive unlock, general desktop control
or offline installation tool is exposed to the chat model. Existing Calculator
demonstration code remains for developer testing, not the conversational tool list.

Reply buffering catches a narrow set of unsupported configuration-change/manual
command recommendations and internet-connectivity promises from DNS-only evidence.
Rejected drafts retry once, then fail closed. This is not semantic verification.
Synthetic model tests still showed unsupported DNS inference and redundant questions;
the conversational model is advisory, with no autonomous repair claim.

## Dependencies and deployment

Previous source is preserved in Backups/SimplicityAI-a8fd330.zip and Git history.
The Conversation-Update bundle retains Kokoro and adds an isolated Whisper Python
runtime, pinned dependencies and model files. PyAV is pinned to 16.0.1 because 19.0.2
was incompatible with faster-whisper 1.2.1's metadata_errors argument. Model sources,
revision, sizes and hashes are in whisper-model-sources.json. App-private MSVC runtime
copies originate from the signed dependency bundled with NumPy, not Windows system
modifications. No drivers or system-wide runtimes are installed automatically.

Use Install-Conversation-Update.cmd after stopping the old server. It verifies model
hashes and backs up previous source; relay credentials and existing logs are retained.
The source/dependency/model payload is approximately 1.34 GiB. Use the newly opened
browser window from Start-ThemHands.cmd to receive the current session token.

## Validation

- Forty-eight Python tests pass, covering chat memory, target gates, no pre-target
  network check, long-check authorization, reply filtering and existing boundaries.
- UI tests cover no forms/default capture, chat submission, audio unlock order,
  automatic speech, Copy, assistant-completion race, cancellation and Talk/Stop.
- Local Whisper transcribed a saved synthetic Kokoro sample exactly in about six
  seconds; this does not establish recognition accuracy on the user's microphone.
- Source and relocated package generated Kokoro WAV successfully and found an input
  device without opening the microphone. The relocated check took about eight seconds.
- Live VM voice conversation, microphone recognition quality and autoplay remain pending.

Sources: https://github.com/SYSTRAN/faster-whisper and
https://huggingface.co/Systran/faster-whisper-small.en .

Voice is half-duplex: the microphone closes during recognition/model inference and spoken playback, then reopens for the next answer during an opted-in Talk session. Use Stop to interrupt playback. A recognized short stop/cancel phrase also ends capture without being sent to the model.
