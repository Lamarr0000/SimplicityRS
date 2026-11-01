"""Opt-in local Windows dictation. No audio files, network API or task execution."""
import json
import os
from pathlib import Path
import subprocess
import threading
import ctypes
from ctypes import wintypes

ROOT = Path(__file__).resolve().parent


def _guard_process(process):
    """Windows closes the microphone child if its server exits unexpectedly."""
    class Basic(ctypes.Structure):
        _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                    ('flags', wintypes.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                    ('active', wintypes.DWORD), ('affinity', ctypes.c_size_t),
                    ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
    class Extended(ctypes.Structure):
        _fields_ = [('basic', Basic), ('io', IO), ('process_memory', ctypes.c_size_t),
                    ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t), ('peak_job', ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    limits = Extended()
    limits.basic.flags = 0x2000
    if not handle:
        raise OSError('Microphone process guard unavailable')
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(handle, int(process._handle)):
        kernel.CloseHandle(handle)
        raise OSError('Microphone process guard could not attach')
    return lambda: kernel.CloseHandle(handle)


class VoiceInput:
    def __init__(self):
        self.lock = threading.RLock()
        self.process = None
        self.generation = 0
        self.state = {'state': 'idle', 'message': 'Click Speak to use the default Windows microphone. Typing is always available.'}

    def snapshot(self):
        with self.lock:
            return {**self.state, 'capture_id': self.generation}

    def start(self, mode='Listen'):
        if mode not in {'Listen', 'Probe'}:
            raise ValueError('Unsupported voice operation')
        with self.lock:
            if self.state['state'] in {'starting', 'listening'}:
                raise ValueError('Voice input is already active')
            self.generation += 1
            generation = self.generation
            self.state = {'state': 'starting', 'message': 'Preparing local speech recognition…'}
            threading.Thread(target=self._run, args=(mode, generation), daemon=True).start()

    def stop(self):
        with self.lock:
            self.generation += 1
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()  # Only this controller's microphone subprocess.
            self.state = {'state': 'cancelled', 'message': 'Voice input stopped. No words were applied.'}

    def _run(self, mode, generation):
        process = timer = guard = None
        try:
            env = dict(os.environ)
            env = {key: value for key, value in env.items() if key.lower() != 'psmodulepath'}
            exe = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            with self.lock:
                if generation != self.generation:
                    return
                process = subprocess.Popen([str(exe), '-NoLogo', '-NoProfile', '-NonInteractive',
                    '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'Voice-Input.ps1'), '-Mode', mode],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8-sig', errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW, env=env)
                self.process = process
                guard = _guard_process(process)
            def expire():
                with self.lock:
                    if generation == self.generation and process.poll() is None:
                        process.terminate()
                        self.state = {'state': 'timeout', 'message': 'Voice capture reached its time limit. Try a shorter sentence or type instead.'}
            timer = threading.Timer(40, expire)
            timer.daemon = True
            timer.start()
            for line in process.stdout:
                try:
                    value = json.loads(line)
                except ValueError:
                    continue
                if value.get('state') not in {'ready', 'listening', 'transcribed', 'no_speech', 'unavailable'}:
                    continue
                with self.lock:
                    if generation != self.generation or self.state.get('state') == 'timeout':
                        return
                    if value.get('state') == 'transcribed':
                        value['text'] = str(value.get('text', ''))[:1800]
                    self.state = value
            process.wait()
            with self.lock:
                if generation == self.generation and self.state['state'] in {'starting', 'listening'}:
                    self.state = {'state': 'unavailable', 'message': 'Voice recognition did not finish. You can type your issue instead.'}
        except Exception:
            with self.lock:
                if generation == self.generation:
                    self.state = {'state': 'unavailable', 'message': 'Local voice input could not start. Typing is available.'}
        finally:
            if timer:
                timer.cancel()
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait()
            if guard:
                guard()
            with self.lock:
                if self.process is process:
                    self.process = None
