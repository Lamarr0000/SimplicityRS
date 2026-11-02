"""Bounded observation of a requested application's foreground window."""
import time


def wait_for_launch(expected, before, foreground, is_window, identify, check,
                    timeout=8, clock=time.monotonic, sleep=time.sleep, activate=None):
    expected_set={expected} if isinstance(expected,str) else set(expected)
    deadline = clock() + timeout
    activation_at = clock() + 2
    attempted_activation = False
    while clock() < deadline:
        check()
        hwnd = foreground()
        # Windows can temporarily have no foreground window during activation.
        if hwnd and is_window(hwnd):
            try:
                identity = identify(hwnd)
            except InterruptedError:
                identity = {'process':None}
            if identity['process'] in expected_set and (identity['process'] != 'mmc.exe' or hwnd != before):
                return identity
        if activate and not attempted_activation and clock() >= activation_at:
            attempted_activation = True
            activate()
        sleep(.1)
    raise InterruptedError('Launch requested, but the requested application did not become foreground within eight seconds; no visual input sent')
