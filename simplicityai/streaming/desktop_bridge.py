"""Owned local Windows-MCP connection. No Codex bridge or remote server."""
import asyncio
import concurrent.futures
import os
import json
from pathlib import Path
import sys
import threading

ALLOWED = {'Snapshot', 'App', 'Click', 'Type', 'Shortcut', 'Scroll', 'ControlStatus'}


class DesktopBridge:
    def __init__(self, allowed=None):
        self.allowed = set(ALLOWED if allowed is None else allowed)
        self.loop = None
        self.client = None
        self.names = set()
        self.ready = concurrent.futures.Future()
        self.thread = None

    async def _serve(self):
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
        self.loop = asyncio.get_running_loop()
        self.stop = asyncio.Event()
        folder = Path('C:/SimplicityAI-Lab/StreamingPrototype/logs')
        folder.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, ANONYMIZED_TELEMETRY='false', WINDOWS_MCP_WATCHDOG='false',
                   WINDOWS_MCP_MAX_TREE_ELEMENTS='100')
        transport = StdioTransport(sys.executable, args=[
            '-m', 'windows_mcp', 'serve', '--transport', 'stdio', '--config',
            str(Path(__file__).with_name('desktop-control.toml')), '--tools', ','.join(sorted(self.allowed))],
            env=env, keep_alive=False, log_file=folder/'desktop-driver.log')
        try:
            async with Client(transport, timeout=25, init_timeout=30) as client:
                self.client = client
                self.names = {item.name for item in await client.list_tools()}
                if not self.allowed <= self.names:
                    raise RuntimeError('Desktop driver did not load the required tools')
                self.ready.set_result(True)
                await self.stop.wait()
        except BaseException as error:
            if not self.ready.done(): self.ready.set_exception(error)
        finally:
            self.client = None

    def _start(self, check_stop):
        if self.thread is None:
            self.thread = threading.Thread(target=lambda: asyncio.run(self._serve()), daemon=True)
            self.thread.start()
        self._wait(self.ready, check_stop, 35)
        if self.client is None: raise RuntimeError('Desktop driver is unavailable')

    @staticmethod
    def _wait(future, check_stop, timeout):
        import time
        deadline = time.monotonic()+timeout
        while True:
            try:
                check_stop()
                return future.result(timeout=.1)
            except concurrent.futures.TimeoutError:
                if time.monotonic() >= deadline:
                    future.cancel()
                    raise TimeoutError('Desktop driver timed out; completion is unverified')
            except BaseException:
                future.cancel()
                raise

    def call(self, name, arguments, check_stop):
        if name not in self.allowed: raise ValueError('Desktop tool is not exposed')
        self._start(check_stop)
        async def invoke():
            result = await self.client.call_tool(name, arguments, timeout=25)
            parts=[]
            for item in result.content:
                if getattr(item,'type','')!='text':continue
                value=item.text
                try:
                    decoded=json.loads(value)
                    if isinstance(decoded,list) and all(isinstance(part,str) for part in decoded):value='\n'.join(decoded)
                except (ValueError,TypeError):pass
                parts.append(value)
            return '\n'.join(parts)[:18000]
        future = asyncio.run_coroutine_threadsafe(invoke(), self.loop)
        try:
            response=self._wait(future, check_stop, 28)
        except Exception as error:
            if any(code in str(error) for code in ('CONTROL_PREEMPTED','USER_CONTROL','TAKEOVER_PENDING')):
                raise InterruptedError('Desktop control returned to the user; no automatic retry') from error
            raise
        if name in {'App','Click','Type','Scroll','Shortcut','Move'} and any(code in response for code in ('CONTROL_PREEMPTED','USER_CONTROL','TAKEOVER_PENDING')):
            raise InterruptedError('Desktop control returned to the user; no automatic retry')
        return response

    def close(self):
        if self.loop and self.loop.is_running(): self.loop.call_soon_threadsafe(self.stop.set)
        if self.thread: self.thread.join(timeout=8)
