"""User-invoked UAC launch of the isolated pilot, never an arbitrary command."""
import ctypes
import argparse
from ctypes import wintypes
from pathlib import Path
import socket
import subprocess


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--validate',action='store_true');args=parser.parse_args()
    python=Path('C:/SimplicityAI-Lab/ThemHands/.venv/Scripts/python.exe')
    script=Path(__file__).with_name('launch.py').resolve()
    arguments=[str(script),'--model','qwen3:8b']
    if args.validate:
        script=Path(__file__).with_name('check_driver_live.py').resolve()
        arguments=[str(script),'--export','--launch-pilot']
    if not python.is_file():raise RuntimeError('Pilot Python is not installed')
    with socket.socket() as probe:
        try:probe.bind(('127.0.0.1',8770))
        except OSError:raise RuntimeError('Exit the current pilot first; another service is using its port.')
    shell=ctypes.WinDLL('shell32',use_last_error=True)
    shell.ShellExecuteW.argtypes=[wintypes.HWND,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.LPCWSTR,ctypes.c_int]
    shell.ShellExecuteW.restype=ctypes.c_ssize_t
    result=shell.ShellExecuteW(None,'runas',str(python),subprocess.list2cmdline(arguments),str(script.parent),0)
    if result<=32:raise RuntimeError('Administrator launch was declined or failed; no automatic retry.')


if __name__=='__main__':main()
