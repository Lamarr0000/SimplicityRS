# Resume checkpoint — November 1, 2026

## Stop here tonight

User is going to bed and requested cleanup, save/push and a checkpoint after the
last VM test. No further development, benchmarks or live tests tonight. User will
shut down guest Windows and then the PC. Do not claim shutdown or the final snapshot
was completed until verified or reported.

Implementation commit: **6ee91c4**. This checkpoint is committed separately.

## Latest user-reported VM results

- Microphone input now works.
- Text replies take approximately **15 seconds**, followed by approximately
  **40 seconds** for the corresponding speech reply. Latency remains unresolved.
- Calculator test worked: actual Calculator opened, performed the operation and
  SimplicityAI spoke the result. User checked it through the taskbar.
- Calculator remained in the background. Foreground activation is not fixed.
- Fresh-session and auto-scroll changes have local tests, but their latest VM
  behavior was not explicitly confirmed in the final report.
- Source validation: **56 Python tests** plus conversational UI/audio/scroll checks
  passed before deployment. Do not substitute that for live VM results.

## Tomorrow's priorities, in order

1. Read this checkpoint and the master resume file; verify current files, VM,
   networking and service state after reboot before changing anything.
2. Investigate the separate text/model and speech delays from actual guest activity
   timings. Model timing and Kokoro preparation timing are logged separately.
   Avoid repeating generic Calculator/SFC benchmarks without a specific need.
3. Move toward a dedicated SimplicityAI application window rather than browser tabs.
   User wants a conversation like this Codex chat, with few visible controls.
4. Study accessible client voice behavior and official OpenAI voice documentation
   for architectural ideas. User asked whether this assistant's voice experience
   can be followed. Do not imply access to private server implementation or promise
   the exact Sol voice. This investigation was deliberately deferred until tomorrow.
5. Bring the app being operated to the foreground so users can watch supported
   actions. Do not fake visible mouse movement as proof of interaction.
6. Confirm live fresh-session and auto-scroll behavior if still needed.

## User requirements and standing permissions

- **SimplicityAI** is the application/interface; **gpt-oss** reasons; **ThemHands**
  supplies connected Windows tools. This is for nontechnical recovery users.
- Speak naturally, ask appropriate follow-up questions, explain what is happening
  and why, use relevant tools automatically, and verify their actual outcomes.
- No guided troubleshooting forms or manual tool-activation step. OS permissions
  and correct Windows-target identification remain necessary.
- One fixed Kokoro playback voice; no voice-selection menu. Preset is internally
  `af_heart`. Typing and text remain available when drivers/voice fail.
- Each new app session and New chat must start fresh. Refresh retains the active
  conversation. This rule does not erase the development project's checkpoint.
- Save, commit and push significant changes when appropriate; user granted standing
  permission. Review private-file exclusions and run relevant checks.
- Put any material the user must paste into the VM in its own fenced Copy block.
- User prefers manual VM steps from this host chat. A separate VM Codex session
  consumed allowance and slowed the PC when all models ran together. Do not start
  that session or concurrent model tests unnecessarily.

## Current code and deployment

- Git: `https://github.com/Lamarr0000/SimplicityRS`, branch `main`.
- Repository: `C:\Users\lamar\OneDrive\Documents\ChatGPT\System Recovery Project`.
- Tracked SimplicityAI source: `simplicityai/prototype`; docs `CONVERSATION.md`.
- Active host lab source: `C:\SimplicityAI-Lab\ThemHands`.
- Guest installation: `C:\SimplicityAI\ThemHands`.
- Guest launcher: `Start-ThemHands.cmd` (legacy filename, visible name SimplicityAI).
- Browser interface: loopback `127.0.0.1:8769`, authenticated session token.
- Latest package: shared `Install-Session-Tools-Update.cmd` and `Session-Tools-Update`.
  This source-only package includes fresh sessions, automatic tools, Calculator
  batch verification and scroll following. Do not reinstall unless needed.
- Previous source files are backed up inside guest `backup-*` directories. Baseline
  source archive: `C:\SimplicityAI-Lab\Backups\SimplicityAI-a8fd330.zip`.
- Existing unrelated recovery working-tree modifications/untracked files are preserved
  and uncommitted. Do not sweep them into a commit or overwrite them.

## Conversation and tool behavior

Current chat tools: health snapshot, network snapshot, SFC `/verifyonly` plus DISM
`/CheckHealth`, and bounded real Calculator operations. No arbitrary shell, repairs,
offline Windows inspection, BitLocker unlock, or general desktop control is exposed.
The physical host cannot be controlled from inside the VM by these tools.

Calculator accepts one simple operation between two nonnegative numbers. It opens
the real app, uses observed UIA buttons, maintains fresh observation IDs, and performs
a separate final reread. Simple explicit numeric requests use a bounded fast path
without model round trips. This is tool automation, not evidence of model arithmetic
or broader diagnostic competence. Host-control requests receive an explicit limitation.

The model chooses connected tools without per-tool activation. Current-Windows
diagnostics still require explicit environment identification. Long verification
checks run only with available OS privilege and never request repair options.

Old saved chat state is no longer loaded on app start. Launcher resets an idle chat
before opening a new window; it refuses to reset an active task. Old diagnostic logs
remain. Within a session, original issue/recent turns support conversation continuity.

The local model has repeatedly made unsupported DNS inferences. Narrow draft checks
withhold some settings-change/manual-command recommendations and DNS-to-internet
promises; they are not semantic validation. No autonomous repair claim is justified.

## Voice and performance

- Input: faster-whisper 1.2.1, small.en at pinned revision
  `d1d751a5f8271d482d14ca55d9e2deeebbae577f`, CPU int8, two threads.
- Capture uses the default input device's native sample rate, live relative signal
  levels and an in-memory WAV for resampling. PyAV is pinned to 16.0.1 because
  19.0.2 was incompatible. No raw microphone audio is saved or uploaded.
- Talk is an explicit half-duplex session: capture, transcribe, model reply, Kokoro,
  then listen again. Stop ends it. Long capture requires review; silence/errors end
  the session. It does not support talking over playback yet.
- Playback: Kokoro ONNX v1.0 standard model, fixed Heart preset, CPU only, two threads.
  Int8 Kokoro was slower and rejected. Web Audio is resumed during user gestures
  before async work; it replaced delayed creation of an Audio element.
- Source and relocated speech diagnostic checks generated valid WAV and found an
  input device. User now confirms actual VM microphone and spoken replies work.
- Kokoro worker is stopped before input/tasks; cold/warm load may be relevant to
  latency, but no cause has been established from the latest guest timings yet.
- `Check-Conversation.cmd` generates a synthetic WAV/probes devices without recording.
  A five-second Test microphone measures signal without loading recognition weights.
- Local assets/dependencies are outside Git; hashes/pinned package lists are tracked.
  Current full conversation payload is about 1.34 GiB; latest update is source-only.

## Host model and relay after a PC restart

Host: i9-9880H, 8 cores/16 threads, about 72 GB RAM, Quadro RTX 4000 8 GB. Guest:
Windows 11 Pro build 26300.9711, 16 GB RAM, one socket/four cores, 128 GB virtual disk.
Models are not all GPU-resident; general response speed remains a limitation.

These were manually started background processes and must be checked after reboot:

- Ollama: `C:\SimplicityAI-Lab\HostTest\Ollama\ollama.exe`, model files
  `C:\SimplicityAI-Lab\HostTest\Models`, model `gpt-oss:20b`.
- Environment for server: `OLLAMA_HOST=127.0.0.1:11434`, `OLLAMA_NO_CLOUD=1`,
  `OLLAMA_VULKAN=false`, `OLLAMA_MODELS` pointing to the existing model directory.
- TLS relay script: `C:\SimplicityAI-Lab\ModelRelay\relay.py`, run with the existing
  managed Python at `C:\SimplicityAI-Lab\ThemHands\runtime\python\cpython-3.14.10-windows-x86_64-none\python.exe`.
- Relay binds VMnet8 `192.168.182.1:11436`, forwards only the intended model to
  loopback Ollama. Guest last verified address `192.168.182.131`, gateway/DNS `.2`.
- Verify the DHCP lease/address before changing configuration. Firewall rule
  `SimplicityAI-VMModelRelay` is narrowly scoped to the VM. Do not broaden it or
  rerun its create-only setup script over an existing rule.
- Private relay configuration/key and guest `model-connection.json` are not in Git.
  Do not print, publish or copy those into source. Existing TLS verification stays on.
- No GPU model or voice model needs downloading again.

## VM, checkpoints and transfer folder

VM: `C:\Users\lamar\Documents\VMs\SimplicityAI Windows 11\SimplicityAI Windows 11.vmx`.
VMware Tools, UEFI, Secure Boot and vTPM are present; user owns encryption password.
Do not use the failed original OneDrive VM.

Read-only inspection at this checkpoint found **one running VM**, the target above,
and **three snapshots**. Latest existing snapshot is the earlier verified-Calculator
checkpoint, before the conversational voice work. End-of-night shutdown and a new
powered-off snapshot are to be performed by the user, not yet confirmed.

Transfer: host `C:\SimplicityAI-Lab\VM-Transfer`, guest
`\\vmware-host\Shared Folders\VM-Transfer`, writable by user authorization.
Older updates/reports are under Archive; cleanup moves, never deletes. The current
session-tools package and this checkpoint remain easy to find.

Preserve SimplicityBRS compatibility baseline and its ISO
`C:\SimplicityBRS-Compatibility\Simplicity-Compatibility-12.iso`.
No TPM, BitLocker, network, recovery disk or BRS settings were changed tonight.
