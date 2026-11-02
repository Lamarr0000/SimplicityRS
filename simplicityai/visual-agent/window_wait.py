"""Bounded observation of a requested application's foreground window."""
import time


def wait_for_launch(expected, before, foreground, is_window, identify, check,
                    timeout=8, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + timeout
    while clock() < deadline:
        check()
        hwnd = foreground()
        # Windows can temporarily have no foreground window during activation.
        if hwnd and is_window(hwnd):
            identity = identify(hwnd)
            if identity['process'] == expected and (expected != 'mmc.exe' or hwnd != before):
                return identity
        sleep(.1)
    raise InterruptedError('Launch requested, but the requested application did not become foreground within eight seconds; no visual input sent')
