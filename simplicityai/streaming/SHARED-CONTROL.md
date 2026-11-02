# Voice Pilot shared controls - 0.7.1 prototype

The host Voice Pilot now connects to the shared control contract without replacing
its existing speech, diagnostic or Calculator engines. Windows and browser input
remain separate adapters, and actual observed results determine completion.

## Windows tools

`desktop_observe` retains its original snapshot/index controls and additionally
returns `structured_controls`: accessible names, roles and automation IDs from the
current foreground window. `desktop_click_control` accepts that snapshot plus an
exact name/role/ID locator. The locator must describe one offered control, then
resolve uniquely again through the shared WindowsAdapter. Enabled state, stable
bounds, runtime identity, foreground and process integrity are checked before the
existing takeover-aware Windows-MCP driver sends one click. The snapshot is consumed
before dispatch; replay is rejected. Existing administration/recovery write blocks
remain. No direct Invoke pattern bypass is used. Old index/type/scroll paths remain.
Read-only identity code was extracted from the preview so this path does not import
its UI or visual model. Shared-module source must be packaged beside streaming.

## Owned browser

New tools: browser_open, browser_observe, browser_act. Ordinary `search_web` now
uses this context and the agent automatically follows it with browser_observe,
instead of treating a native Edge launch as page evidence. After every named
Windows or browser mutation, a fresh relevant observation is forced before the
next model decision/completion report. The prompt prefers structured actions.

A separate worker uses the existing isolated Playwright runtime under
C:/SimplicityAI-Lab/ControlAdapter/.venv. It launches installed Edge with a fresh
temporary context. There is no personal profile attachment, persistent debugging
port or cloud inference. Private stdin/stdout pipes carry bounded JSON with request
IDs; a Windows job owns the worker and browser descendants. Browser permissions
are not approved, downloads are not accepted and popups are closed. Runtime errors
are recorded rather than retried as if no action occurred.

Browser observations contain URL/title and bounded accessibility structure. A
snapshot expires after60s, changes page URL invalidate it, and mutations consume
it. Exact role/name/ID lookup is followed by Playwright actionability checks.
Supported operations are click for button/link/tab and fill for textbox/searchbox.
Optional expected_text is an observable postcondition, not universal task completion.
HTTPS/about:blank only, no credentials in URLs, password/file/hidden fields refused.
Account/security/upload/consequential control names are refused. These constraints
and model policy are not a hardened browser sandbox or semantic proof that every
ordinary-looking form is harmless. No reviewed consequential workflow is added.
No arbitrary model JavaScript, uploads, user-profile data or authentication control.

Readiness/observation can retry; dispatched input is never automatically replayed.
No-input refusals preserve the context and invalidate its snapshot so the model can
observe again. Unknown/sent-action failure, timeout or cancellation discards the
owned context. Observation never creates/reopens a missing browser. Stop, New chat
and Exit close it. The desktop driver's ownership monitor is checked before and
through browser mutations; user takeover stops without retry. An initial short wait
allows the user's just-completed input to become idle. No UAC bypass or policy change.

## Verification and current runtime

70 streaming regressions and42 shared/visual tests pass. Tests include outside-host
scope, schema boundaries, action-paused tools, forced browser follow-up, takeover,
pre-request cancellation and no implicit reopen. Real desktop Voice Pilot path
performed Calculator clear/Seven/clear with independent display reads and rejected
consumed snapshot reuse. Real owned-worker integration used a blocked-network local
fixture: fill, click/result, unsafe URL and consequential-control rejection, context
preservation on no-input refusal, cancellation and owned descendant shutdown pass.
No microphone or physical audio was used and no new model benchmark was run.
Reports: external ControlAdapter/voice-desktop-check.json and
voice-owned-browser-check.json. These prove adapter/router checks, not unrestricted
agent planning or a real user's voice session across arbitrary websites.

Existing local Ollama was started with its documented loopback/model directory,
cloud disabled, and version/tag checks verified qwen3:8b is available. No firewall,
relay, power or Windows security settings changed. Voice Pilot was launched and
/health verified0.7.1-prototype. UI independently showed Ready, Talk, and disabled
Mute mic (capture off). It is left open for the user's live interaction. The normal
0.6.3 installation, VM/shared package and BRS remain unchanged. User enables Talk and
any microphone permission themselves; no UAC was required for these checks.
