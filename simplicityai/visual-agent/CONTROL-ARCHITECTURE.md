# Shared control architecture

Implemented in the isolated desktop preview, November 2, 2026.

The same ControlSession contract supports native Windows controls and an owned
Playwright page: find a unique locator, wait for visibility/enabled/stable geometry,
re-resolve before the operation, perform once, then poll an explicit observable
postcondition when supplied. Readiness and verification can retry; a dispatched
action is never replayed automatically. Unknown action outcome stops the caller.
Ambiguous locators cause no input. Cancellation checks run throughout polling.

## Desktop preview connection

The model now receives a bounded catalog of current Windows control names, roles
and automation IDs, alongside its screenshot. It can emit:

    click_control(name='Seven', role='button', id='num7Button')

ID is optional; name/role/ID filters are exact and must resolve to one live control.
WindowsAdapter refreshes the UIA tree, requires the same runtime identity and
stable enabled bounds, and sends the current control-center click through the
existing Windows-MCP bridge. Existing foreground/integrity/password/protected-app,
Calculator/Notepad case guards, cancellation and takeover checks remain active.
The Windows adapter currently supports click; existing focused typing and other
preview actions continue through their original guards. It does NOT call UIA
Invoke directly, which would bypass the input driver's ownership gate.

Screenshot coordinate actions remain available for inaccessible controls. Missing
or ambiguous structured locators return no-input feedback; they are not silently
converted into guessed coordinates. This is a locator-based desktop adapter,
not Playwright controlling native Windows or a hardened input sandbox. UIA calls
are cooperatively bounded; individual provider calls can still stall. Snapshot/
input races and inconsistent application accessibility remain limitations.

Per-action result states distinguish action sent, no postcondition requested,
verified postcondition and unverified result. Global acceptance completion still
uses independent task verification before another model action. Dispatch success
alone is never a task-completion claim. Repeated identical Calculator actions with
different measured progress are handled by state-aware tracking rather than the
older coordinate-only repetition guard.

## Browser adapter

BrowserAdapter uses Playwright locators and its actionability checks with the
same contract; supported actions are click and fill. Accessible role/name maps to
get_by_role; generic control ID maps to the page's data-testid. An owned page/
context must be supplied by the caller. No personal browser profile, existing
browser account, arbitrary model-authored JavaScript or persistent remote-debug
port is opened by this adapter. Page permissions/navigation policy belong to that
caller. It is not yet routed from the Voice Pilot or attached to arbitrary user
Edge windows. This is the working browser backend for future controlled-browser
routing, not a claim that main-app browser integration is complete.

Optional dependencies are pinned in requirements-browser.txt. Installed isolated
runtime: C:/SimplicityAI-Lab/ControlAdapter/.venv. Existing voice dependencies and
vendor Windows-MCP remain unchanged. Browser check uses installed Edge headless,
a fresh temporary context, an in-memory local page and blocked network requests.
No new browser binary or personal profile was installed/copied.

## Verification

42 automated tests plus Python compilation pass. Shared-engine tests cover
ambiguity, hidden controls, stale replacement identity, postconditions, and no
replay after a potentially sent action. Model action decoding is literal AST only.
check_windows_adapter.py exercised real Calculator clear -> Seven -> clear through
the shared engine and existing guarded driver, independently reading each display.
check_browser_adapter.py exercised local-page fill, click/result and ambiguity
rejection in real Edge. Both integration checks passed. Detailed reports:
C:/SimplicityAI-Lab/ControlAdapter/windows-check.json and browser-check.json.
These are adapter functional checks, not a model-planning benchmark. Per user's
steering no new screenshot arithmetic/model-performance trial was run. No claim
that the previous UI-TARS planning failure is fixed. No microphone or settings
changes. Main Voice Pilot/normal app/VM/BRS remain unchanged.

## Primary design references

- https://playwright.dev/python/docs/locators
- https://playwright.dev/python/docs/actionability
- https://playwright.dev/python/docs/browsers
- https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-controlpatternsoverview
- https://github.com/microsoft/playwright-mcp

Playwright is used for browser operations; its architecture informs the Windows
contract. The existing Windows-MCP MIT source supplies UIA inspection and guarded
input, with its existing notices preserved. No Playwright implementation was copied
into the Windows adapter.
