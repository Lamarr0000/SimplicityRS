"""Narrow ThemHands adapter using Windows-MCP's MIT-licensed UIA library.

Only Calculator buttons are exposed. No shell, arbitrary keys, or coordinates.
All UIA objects stay on one apartment/thread; callers serialize access.
"""
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import psutil

BUTTONS = {
    **{f"num{i}Button": str(i) for i in range(10)},
    "plusButton": "+", "minusButton": "-", "multiplyButton": "×",
    "divideButton": "÷", "equalButton": "=", "clearButton": "Clear",
    "decimalSeparatorButton": ".", "negateButton": "+/-",
}


class Calculator:
    def __init__(self):
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ThemHands-UIA")
        self.worker.submit(self._initialize).result(timeout=30)

    def _initialize(self):
        import windows_mcp.uia as uia
        self.uia = uia
        self.version = 0
        self.selected_handle = None
        self.last_state = None

    def _window(self):
        windows = []
        for control in self.uia.GetRootControl().GetChildren():
            try:
                # UWP windows can belong to ApplicationFrameHost; validate the
                # actual child app process instead of trusting the frame title.
                candidates = [control, *control.GetChildren()]
                def is_calculator(candidate):
                    process = psutil.Process(candidate.ProcessId)
                    path = process.exe().lower().replace("/", "\\")
                    return ("\\program files\\windowsapps\\microsoft.windowscalculator_" in path
                            and process.name().lower() in {"calculatorapp.exe", "calculator.exe"})
                if any(is_calculator(candidate) for candidate in candidates):
                    windows.append(control)
            except (psutil.Error, OSError):
                continue
        if not windows:
            self.selected_handle = None
            return None
        selected = next((w for w in windows if w.NativeWindowHandle == self.selected_handle), None)
        # UIA root order is foreground/Z order; bind once, then keep that exact
        # Calculator window even if the user changes foreground focus.
        selected = selected or windows[0]
        self.selected_handle = selected.NativeWindowHandle
        return selected

    def _walk(self, control, depth=0):
        yield control
        if depth < 14:
            for child in control.GetChildren():
                yield from self._walk(child, depth + 1)

    def _observe(self):
        window = self._window()
        self.version += 1
        if window is None:
            self.last_state = {"open": False, "observation": self.version, "buttons": []}
            return self.last_state
        buttons, display, expression = [], None, None
        for control in self._walk(window):
            aid = control.AutomationId
            if aid in BUTTONS:
                buttons.append({"id": aid, "label": control.Name, "meaning": BUTTONS[aid]})
            elif aid == "CalculatorResults":
                display = control.Name
            elif aid == "CalculatorExpression":
                expression = control.Name
        self.last_state = {"open": True, "title": window.Name, "window_handle": self.selected_handle, "observation": self.version,
                "display": display, "expression": expression, "buttons": buttons,
                "usable": display is not None and bool(buttons)}
        return self.last_state

    def _open(self):
        before = self._window() is not None
        if not before:
            subprocess.Popen([os.path.join(os.environ["WINDIR"], "System32", "calc.exe")],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, shell=False)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            state = self._observe()
            if state.get("usable"):
                return {"already_open": before, **state}
            time.sleep(.25)
        raise RuntimeError("Calculator did not expose its expected controls within 15 seconds.")

    def _press(self, button_id, observation):
        if button_id not in BUTTONS:
            raise ValueError("Button is outside the Calculator allowlist.")
        if type(observation) is not int or observation != self.version:
            raise ValueError("Stale observation. Observe Calculator again before acting.")
        previous = self.last_state
        current = self._observe()
        fields = ("open", "window_handle", "display", "expression", "buttons")
        if not previous or any(previous.get(key) != current.get(key) for key in fields):
            raise ValueError("Calculator changed since the model observed it. No button pressed; observe again.")
        window = self._window()
        if window is None:
            raise RuntimeError("Calculator closed; no action performed.")
        matches = [c for c in self._walk(window) if c.AutomationId == button_id]
        if len(matches) != 1 or not matches[0].IsEnabled:
            raise RuntimeError("Expected exactly one enabled Calculator button.")
        # Invokes the actual app button, without synthetic keyboard input.
        matches[0].GetInvokePattern().Invoke()
        time.sleep(.12)
        return {"pressed": BUTTONS[button_id], **self._observe()}

    def call(self, name, args):
        functions = {"open_calculator": self._open, "observe_calculator": self._observe,
                     "press_calculator_button": self._press}
        if name not in functions:
            raise ValueError("Unknown tool")
        return self.worker.submit(functions[name], **args).result(timeout=35)
