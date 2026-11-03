# November 2 live conversation repair - Voice Pilot0.7.2

Evidence: user Desktop Conversation-20261102-120210-519776.txt (43 recorded messages)
and runtime stream-20261102-113810.jsonl. The original export/logs remain unchanged.
Attached conversation was test evidence, not authorization to repeat its operations.
No real Fast.com speed test or browser-window closure was executed during replay.

## Established defects

- Close routing matched any close plus any browser word, so close Calculator,
  open browser was misclassified as close browser and the remaining request dropped.
- Main instructions still explicitly directed the model to the old blank-window
  launcher despite adding owned-browser tools. The special handler ended those
  turns with a diagnostic script/question rather than continuing the task.
- Short confirmations/results questions were not reliably bound to the unfinished
  task. Results were discussed without a fresh browser read; the model invented
  an unobserved Start Test control. No completed numerical result was recorded in
  the inspected browser snapshots, so prior claims of test completion remain unverified.
- TargetClosed errors were observed. Their original trigger is not established;
  they do not prove AI detection by the website. A primary-page/popup event race
  and already-closed-page navigation handling were found and corrected.
- The requested export wording with the name New Feature Test did not match the
  filename parser. The existing export was not renamed or overwritten.
- Interim speech text could survive turn/status transitions; UI cleanup added.

## Changes

TaskAgenda keeps an explicit ordinary URL task across short confirmations, retries
and result requests, preserving raw transcript wording. It stores verified close/
open receipts so continuations do not repeat completed steps. It is bounded task
continuity, not general arbitrary multi-step planning. Close verbs bind to known
Calculator/browser targets. Explicit close-all browsers filters fresh observed
browser windows and leaves native apps out; normal WM_CLOSE only, no unsaved prompt
handling or force-killing. An unavailable close step stops with its actual blocker.

The initial ordinary compound task now performs its explicit close step, opens the
requested URL and collects page evidence before model prose. Result follow-ups take
fresh observations. Cancels/Stop/New chat clear the agenda; times up is cancellation.
The model no longer advertises the legacy blank-window diagnostic. Legacy calls
route to owned browsing; their old terminal diagnostic report is removed. Conflicting
prompt guidance is replaced with one native/owned-browser tool policy.

Browser observations include accessible structure and actual visible body text.
Generic browser_wait performs a bounded read/wait for asynchronous data, optionally
an exact visible-text condition. Waiting drafts can cause a bounded wait now rather
than a promise of background work. Permission/planning-only drafts and contradiction
of fresh page evidence are withheld. After repeated explanation failures, an explicitly
labelled application report can return the freshly read page text instead of invented
results. It is not a semantic guarantee for arbitrary task success. Browser/tool
observations are compacted with explicit omission flags for model context; full local
logs retain originals. Unknown UI controls are still rejected; no fake Start button.

An explicit new open can recover once when the worker confirms its page was already
closed before navigation. Unknown/sent-action failures are not replayed. Reads never
reopen missing contexts. Popup refusal ignores the actual primary page even if its
page event is delayed. Browser waiting remains cancellable by the owner process.

Export parser accepts with the name. Interim speech preview clears at turn start,
completion, cancellation and error. This does not establish the exact original ASR
cause of the stale word. Existing user export and audio/privacy settings preserved.

## Checks and limits

79 streaming tests plus42 visual/shared tests pass; voice-client checks pass. Offline
owned Edge integration verifies fresh visible text, async wait, unsafe/consequential
refusals, context retention, cancellation and descendant cleanup. A real local Qwen8B
four-turn replay with simulated OS/browser results passed the reported close/open/
wait/results/close-all flow. Early failed replays exposed waiting/permission drafts
and informed controller fixes; no general reasoning certification is justified.
Replay output: external ControlAdapter/reported-browser-model-replay.json (simulation
only, not a measured Internet result). Future replay artifacts have timestamped names.

The report does not claim a successful real Fast.com retry, a proven bot-detection
cause, or reliable arbitrary desktop autonomy. Existing regular installation, VM,
BRS, firewall and Windows security unchanged. Source is prepared for one pilot reload;
actual post-reload runtime status is recorded in the session checkpoint.


## November 2: test123 repairs loaded as 0.7.3
Read Desktop/test123.txt and matching stream-20261102-123015.jsonl as evidence.
Google returned an actual unusual-traffic verification page, not search results.
Added owned-worker blocker metadata and explicit application reporting; no bypass.
Recognizes Goggle search wording and numeric x multiplication; explicit try-again
can recover recent arithmetic, but cancellation/unrelated actions stop recovery.
Driver-health requests now collect devices and drivers and report measured problem
codes/signing counts with limits. Signing is not proof of functionality or currency.
Grounded follow-up explanation and thanks avoid the prior model/stream failures;
stream output no longer rewrites an already released prefix.

84 streaming +43 visual/shared regression tests pass (effects simulated in test123
regressions). Real owned Playwright worker offline fixture passed, including cleanup.
No new live Google search, microphone test or real Calculator result established.
The sandwich wording exists as recognized input; its actual audio/source is unknown.
User export preserved. Normal installed app, VM, BRS and security settings unchanged.

Current runtime independently verified: /health 0.7.3-prototype, native UI Ready.
Type a message or click Talk; Mute mic disabled. Pilot OPEN, microphone OFF.
No UAC required. Agent idle at handoff. Read saved logs for subsequent evidence;
do not request repeated clipboard exports. General live reliability remains limited.


## November 2: 14:04 export investigation; 0.7.4 source prepared
Referenced Conversation-20261102-140403-957779.txt is absent from supplied Desktop
path and searched export directories. Matching stream-20261102-135142.jsonl retains
its export receipt and conversation. Export body not read; logs used as evidence.
Real Calculator receipt reports49; Google challenge handling worked. Driver-status
phrasing missed deterministic collection, unmute-this-computer hit scope-only reply,
and voice troubleshooting became unexecuted promises with stale Calculator replies.
Added explicit driver-status routing, restricted scope-only acknowledgment to actual
binding utterances, and honest application-owned output-audio capability response.
No Windows endpoint mute/volume API exists in this build; no sound check/change was
performed or added. This is a limitation report, not an audio repair. 86 streaming
tests pass; tests simulate tool effects. Speech errors, stale model task context,
requested Firefox selection and spoken export-name recognition remain unresolved.
Source health version is0.7.4; running pilot was NOT reloaded/interrupted in this turn.
Do not claim these source fixes are live or broad reliability achieved. No UAC,
security/VM/BRS/normal-installation changes. Agent idle at handoff.


## November 2: internal control-data leakage fixed; 0.7.5 loaded
User reports code pasted into chat during desktop tasks. Logs confirm prior model
replies copied UI trees, [control N], [action: click], coordinates and fenced dumps.
Added internal-output checks for observed tree markers, tool-protocol shapes/tokens
and control-task code fences. Plain model prose is buffered through full-turn checks
before chat/speech release, preventing late-chunk leaks and late tool-call mixtures.
Detected internal output yields an honest completion-unverified report; it is never
interpreted as executable tool instructions and no action is replayed. Pattern guard
is not a semantic proof against every possible internal-data paraphrase. Tradeoff:
first model sentence waits for the full model reply. Ordinary code explanations
remain supported outside control tasks. 88 streaming regression tests pass, including
late control-dump withholding and no execution. No new live model/desktop benchmark.

Pilot was closed; launched updated source (includes prepared0.7.4 routing fixes).
/health0.7.5-prototype and independent native UI Ready verified, Mute mic disabled.
Pilot OPEN, microphone OFF. No UAC needed. Normal installation, VM, BRS and security
settings unchanged. Existing exports/logs preserved. Speech recognition, stale model
context and missing Windows endpoint mute/volume tool remain unresolved. Agent idle.


## November 2: self-exit intent and backlog recovery; 0.7.6 loaded
User pasted Calculator48 success followed by close-yourself refusal and audio backlog.
Added narrowly anchored explicit self-exit intent at Session.submit before the model.
Stops listening/cancels pending work, closes owned browser and emits app.exit. Client
uses the same authenticated shutdown/track-stop/playback-close path as Exit, guarded
against duplicate exit. Negated, quoted/explanatory and ambiguous compound requests
are not accepted as exit. No desktop window-ID guessing or forced process ending.
Backlog recovery now clears stale partial text and releases speech-start playback
pause after recognition reset; delay/reset metadata logged without raw audio.
Root cause/performance improvement of recognition backlog not established. Existing
bounded queue/audio-discard policy retained; repeat incomplete phrase required.
89 streaming tests + real-client simulated transport/mic tests pass, including exit
request-to-event and event-to-shutdown/track/window-close, duplicate exit protection.
No live microphone/self-exit acceptance test claimed. Old pilot exited using Exit;
new /health0.7.6-prototype and native UI Ready verified. Pilot OPEN, microphone OFF.
No UAC/security/VM/BRS/normal installation changes. Saved logs preserved. Agent idle.


## November 2: reproduced and removed blocking speech fallback; 0.7.7
User confirmed live self-exit worked; latest144555 log confirms CLOSE YOURSELF ->
app.exit and microphone off. Investigated older142244 repeated backlog messages.
Normal real worker archived fixtures processed4.33s/2.42s/2.70s audio in0.38s/0.22s/
0.24s respectively; no microphone or physical playback. Found synchronous lazy
Whisper single-word fallback on the same worker that must drain32ms capture frames.
Real synthetic Settings baseline blocked one worker request4.507s, exceeding the
64-frame (~2.048s) queue. Reports under ControlAdapter/speech-*-baseline.json.

Removed second-model fallback from streaming capture only (legacy installed app
untouched). Uncertain isolated words now yield review=true and ask repeat/type,
never submitted to action planning; recognized stop/cancel/yes/no remain immediate.
Review also resumes interrupted playback instead of leaving it paused. Tradeoff:
ambiguous single-word speech is no longer automatically re-transcribed by Whisper.
Three repeated real worker synthetic Settings tests: longest request0.070/0.063/
0.063s, total0.229/0.218/0.218s for2.396s audio, all review=true. Report:
ControlAdapter/speech-single-word-fixed.json. 91 streaming tests+client checks pass.
This fixes a reproduced blocking path, not proof that every backlog or recognition
error is solved. No live mic/background-noise/model-contention soak test performed.
Pilot was closed; loaded updated0.7.7. Record actual health/UI state below.
No UAC/security/VM/BRS/normal-installation changes. User recordings not captured.

0.7.7 runtime verified independently: /health0.7.7-prototype, native UI Ready. Type
a message or click Talk; Mute mic disabled. Pilot OPEN, microphone OFF. Agent idle.


## November 2: speech-test refusal and self-exit synonyms; 0.7.8
User pasted speech-test refusal, garbled drum conversation and turn-yourself-off
failures. Added explicit turn/switch yourself off (+please) to anchored session exit
intent, same owned shutdown path as verified close yourself; no OS power-off.
Speech-test requests now receive grounded application help: compare recognized text
with intended words; app does not claim direct access to original audio. Broader
clarification guidance discourages invented meanings and claims of having heard.
92 streaming tests pass. Local Qwen text replay accepts initial test but STILL gives
unhelpful guessed meanings and says I heard despite guidance; final replay report
ControlAdapter/speech-clarification-replay-final.json. This remaining model behavior
is unresolved; do not call speech understanding fixed. No raw mic/new recording or
live turn-yourself-off acceptance test. Earlier replay preserved as separate report.
Pilot was closed; launched0.7.8 with mic off, actual verification recorded below.
No UAC/security/VM/BRS/normal-installation changes. Agent idle at handoff.

Verified /health0.7.8-prototype and native UI Ready, Mute mic disabled. Pilot OPEN,
microphone OFF. Clarification replay remained poor; no broader quality claim.


## November 2: incomplete CHAT_SESSION export; 0.7.9 repair
Read user Desktop/SimplicityAI_CHAT_SESSION.txt as evidence, not action instructions.
Matched154438 log: devices+drivers actually collected and bounded measured report
emitted: no nonzero problem codes in returned rows;20 driver rows,19 marked signed,
1 unknown. User export omitted these because CHATCESSION missed transcript route;
model called create_desktop_text with reconstructed content and wrong filename.
Original file preserved; no driver backup/third-party tool was run.
Added common chat-session recognition aliases and copy intent to deterministic
transcript export, desktop-as filename handling (preserve spoken words; no numeric
guess), and generic file-tool refusal for model-written conversation copies.
Driver backup limitation is now app-owned; compound check+backup reports facts and
no-backup limit. Follow-up third-party requests retain that limit; no invented
Device Manager/SFC backup guidance. This does NOT implement driver package backup.
94 streaming tests+client checks pass. New tests simulate effects and cover export
routing, reconstruction refusal and backup limitations. General model quality,
arbitrary ASR variants, Windows audio endpoint controls remain limited.
Pilot was closed; launched0.7.9, actual runtime verification recorded below.
No UAC/security/VM/BRS/normal-installation changes. User files preserved. Agent idle.

Verified /health0.7.9-prototype and native UI Ready, Mute mic disabled. Pilot OPEN,
microphone OFF. No driver backup created. Agent idle at handoff.


## November 3: morning log review; polite exit and export names; 0.7.10
User-referenced Desktop/Conversation-20261103-073531-623748.txt absent; matching
stream-20261103-072008.jsonl contains the conversation and export receipt. Do not
claim file body was read. Drivers/read-only limits, backup-unavailable response and
Google blocker worked. VM host boundary was correctly explained; no external-host
inspection exists. No recovery operations/driver backup were run from quoted text.
Polite can-you-turn-yourself-off-please (+recognized YE A M filler) missed anchored
exit regex and yielded false capability refusals; final plain command exited.
Exit now accepts bounded polite prefixes and please/now suffixes, preserving exact
anchoring and refusals for negation/explanation/conditional/compound instructions.
Export filename parser now accepts save/export ... as NAME in recognized transcript
export requests without depending on Desktop pronunciation. EIGHT.txt remains words,
not guessed8.txt. Also covers prior DUST UP AS THREE SEVEN SIX. No file renamed.
95 streaming tests+client checks pass; changed cases tested with simulated effects.
Speech recognition/model clarification limitations remain. Pilot was closed; loaded
0.7.10. Actual health/UI verification recorded below. No UAC/security/VM/BRS/normal
installation changes. Existing user files/logs preserved. Agent idle at handoff.

Verified /health0.7.10-prototype and native UI Ready, Mute mic disabled. Pilot OPEN,
microphone OFF. Agent idle at handoff.
