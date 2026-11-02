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
