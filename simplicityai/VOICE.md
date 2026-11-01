# Local voice prototype

Voice input is optional, initiated by **Speak my issue**, and stops after one recognized
phrase or a time limit. The draft must be reviewed and explicitly added to the issue
description. It cannot select a target, start a tool, or authorize a repair. No microphone
is activated on page load or during the availability probe. Typing remains available.

## Implementation

- `Voice-Input.ps1` loads the installed Windows System.Speech engine, preferring en-US,
  and uses its default audio input with a dictation grammar. No online recognition API,
  uploaded audio, model download, recorded audio file or GPU inference is added.
- `voice.py` runs only that fixed script with Probe or Listen. Capture is bounded to
  forty seconds by the controller; Stop terminates only its owned child. A Windows job
  closes the child if the server exits unexpectedly. Leaving the browser page also
  requests cancellation. The availability probe verifies engine presence, not drivers,
  microphone permissions, audio routing or transcription quality.
- Authenticated loopback endpoints provide status, probe, capture and cancellation.
  Starting a task is rejected during capture. Captured words stay in memory until the
  user elects to use them; submitted task descriptions use the existing local logs.
- Browser speech synthesis offers only voices with `localService === true`. Users
  select a local voice and click Read next step aloud or Read reply aloud. Playback
  never starts automatically; Stop speaking cancels it. No exact ChatGPT voice is
  bundled or promised. If no local voice is offered, text remains available.

## Requirements and limits

Requires installed Windows speech components, a compatible speech language, default
microphone and speaker devices/drivers, Windows permissions, and working VMware audio
input/output when tested in a VM. No drivers, languages or permissions are installed
or changed automatically. The Windows recognizer may be unavailable or inaccurate on
some installations; fallback is typing, not a silently substituted cloud service.

Host validation: installed en-US engine found through the script and controller without
activating a microphone; real Windows child cleanup test passed; mocked capture,
cancellation and endpoint tests passed. Browser-handler checks verify review-before-use
and rejection of remote playback voices. Thirty-seven Python tests pass.

Still pending: guest engine availability, live microphone transcription, local speaker
playback, browser visual review, recognition quality and disconnected-network validation.
No actual user audio was captured during host development tests.

## Guest deployment

Stop the existing server (elevated if previously started as administrator), run the
shared-folder `Install-Voice-Update.cmd`, then start the normal `Start-ThemHands.cmd`
and refresh the page. This adds no diagnostic task or scan. First click **Check voice
availability**. Only click **Speak my issue** when ready to test the VM microphone.

## Primary references

- [Microsoft: Recognize and timeout semantics](https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine.recognize?view=netframework-4.8)
- [Microsoft: default audio input](https://learn.microsoft.com/en-us/dotnet/api/system.speech.recognition.speechrecognitionengine.setinputtodefaultaudiodevice?view=netframework-4.8)
- [MDN: local versus remote speech-synthesis voices](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService)
