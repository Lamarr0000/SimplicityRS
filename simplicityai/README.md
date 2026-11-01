# SimplicityAI prototype

SimplicityAI is the application and interface; gpt-oss provides local reasoning;
ThemHands provides scoped Windows interaction and diagnostic tools. Model weights
have not been modified. This source snapshot preserves the working prototype layout;
extracting ThemHands into an independent package is future work.

## Source layout

- `prototype/`: interface, agent loop, Calculator UI Automation, fixed read-only Windows collectors, and tests.
- `model-relay/`: authenticated TLS relay from the Windows VM to host Ollama.
- Existing repository folders remain the SimplicityBRS recovery environment source.

The running lab remains under `C:\SimplicityAI-Lab`; committing this source does not
change or redeploy the lab or guest. Start-ThemHands.cmd retains its compatibility
filename; the visible interface is branded SimplicityAI.

## Dependencies and local setup

Tested using Windows Python 3.14.10, psutil 7.2.2, comtypes 1.4.17, Ollama 0.40.13
and gpt-oss:20b. The Calculator tool imports the UIA library from CursorTouch's
Windows-MCP, commit `7fd39b4c1551d4d9da33d55c486ac5c4c6e2cf41`, version 0.8.8:
https://github.com/CursorTouch/Windows-MCP
Retain its MIT license and the UIA component's upstream Apache attribution when
installing or redistributing it. Downloaded vendor code is deliberately not committed.
Make that checkout's `src` directory available on Python's module search path.

The current launcher expects an isolated `.venv\Scripts\python.exe` in the source
layout; the VM deployment instead supplies a portable `runtime\python.exe` and a
matching launcher. The portable runtime and dependencies are not in Git.

Run tests from `prototype` with the prepared environment:

```text
python -m unittest test_health test_boundaries
```

Local mode uses loopback Ollama. Guest mode requires a privately provisioned
`model-connection.json` and trusted relay CA. The relay requires private configuration,
a server certificate/key and a narrowly scoped firewall rule. These are intentionally
absent. The setup script contains lab-specific paths and IP addresses: inspect before
using on another machine. This is source preservation, not a one-click installer.

## Verified and limited behavior

VM testing verified Calculator actions and the automatic separate reread after
equals (15 × 6 displayed 90 twice). Read-only health collection includes bounded
System-event excerpts, counts and timestamps. Normal guest permissions left BitLocker,
TPM and Secure Boot status unknown; no repairs were indicated or performed.

The model mixed separate event counts during testing. Exact facts now appear directly
in the interface; health prose is buffered and drafts containing digits retry once,
then fail closed. This is a formatting guard, not semantic verification or proof of
diagnostic reliability. Twenty-two boundary and behavior tests passed locally.

The reply panel and Copy buttons passed JavaScript syntax checking; guest visual and
clipboard verification remains pending. No general Windows repair, arbitrary desktop
control, offline Windows inspection, voice or vision capability is claimed.

Never commit VM disks, Windows images, model weights, credentials, recovery keys,
certificates/private keys, session URLs or diagnostic logs. Review staged files before
each commit; ignore rules are an extra safeguard, not a secret scanner.

Network extension: fixed read-only adapter configuration plus an explicit-server Windows A-record query for microsoft.com, bounded by an eight-second job wait. It tests only the first configured IPv4 DNS server. No DNS cache flush or configuration changes; upstream resolver caches may be used. Host smoke check succeeded; guest test pending. Exact network values appear in Measured facts. No internet reachability diagnosis is implied.

Network report mode now bypasses the model and renders a deterministic network-only report with explicit limits and scripted provenance. This responds to the guest model drifting into unrelated historical events and spelling out numbers to evade the digit-format guard. The guard is not semantic validation. Saved guest evidence confirmed DNS succeeded through the configured resolver; no full connectivity claim. Twenty-five tests pass, including no model calls in network mode. The fixed collector still gathers the broader health snapshot locally; only network facts enter the network report. Guest deployment pending.

A separate SIMULATION DNS-timeout mode uses synthetic documentation-range addresses and a reserved test domain. It calls neither the model nor Windows collectors, explicitly labels evidence as synthetic, and presents a bounded scripted interpretation with unproven causes and conditional next-check outcomes. This is workflow validation, not AI reasoning success. Twenty-six tests and isolated clipboard-handler checks pass; guest simulation test pending.

Current-Windows integrity mode: fixed DISM /Online /Cleanup-Image /CheckHealth followed by SFC /verifyonly. No repair options, model commands or offline target accepted. Administrator access required; no commands run otherwise. VM-only helper Start-SimplicityAI-Admin.cmd launches portable runtime with user-approved elevation after stopping the existing server. CheckHealth reads recorded corruption status, not a fresh full scan. SFC verifies protected files. Diagnostic log writes may occur. Unrecognized/localized output is marked for review, not clean; recognized clean phrases additionally require exit code zero. Stop prevents the next command but lets an active check finish. Twenty-nine tests pass; real guest verification pending. No host checks executed.

Guest current-Windows verification completed Nov 1: DISM CheckHealth exit zero/no corruption flagged in 0.9s; SFC verifyonly exit zero/no integrity violations in 273.5s. No repairs requested. Reply formatter now omits raw progress and preserves detailed output in evidence/logs. Tested against supplied guest outputs without rerunning tools. Thirty-one tests pass.

Guided UI offers browsing/crash/startup problem choices, explicit current-Windows versus other-installation target, and symptom context. Show my next step prepares an explanation and selects a fixed tool but never starts it. Another installation or nonbooting Windows is unsupported and blocks Start; no offline work is implied. Browser-handler tests cover routing and target restriction, plus panel clipboard isolation. User symptoms are recorded, not automatically diagnosed. Guest visual review pending; no repeat integrity scan needed.

Optional voice prototype: see VOICE.md for local Windows input, review-before-use, local playback selection, requirements, test evidence and guest limitations. No microphone was used during host development. Guest voice testing pending.

Latest interface: one message composer with optional microphone, contextual follow-up questions and explicit Run this check. Advanced modes/evidence are collapsed. Playback is one fixed local Kokoro voice, with no selection menu. See VOICE.md and model provenance. Forty-one Python tests and conversational UI checks pass; guest appearance/audio review pending.

Current main interface is a true local-model conversation, replacing the guided forms. Optional Talk sessions use local Whisper input and automatic Kokoro replies; chat saves locally. See CONVERSATION.md for scope gates, dependency pins, test results and remaining model/guest limitations. The model is still gpt-oss, not the Codex assistant. No autonomous repair capability is claimed.
