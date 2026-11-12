"""PERF-511: leitores não bloqueantes, EOF removido e recuo por seguidor."""
import io
import os
import selectors
import subprocess
import time
from types import SimpleNamespace


class Followers:
    def __init__(self, commands, clock=time.monotonic):
        self.clock = clock
        self.selector = selectors.DefaultSelector()
        self.items = {name: dict(command=cmd, process=None, due=0, delay=5,
                                buffer=b'', started=0) for name, cmd in commands.items()}

    def _retire(self, item):
        proc = item['process']
        if proc:
            self.selector.unregister(proc.stdout)
            proc.stdout.close()
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        item['process'] = None
        item['buffer'] = b''
        if self.clock() - item['started'] >= 60:
            item['delay'] = 5
        item['due'] = self.clock() + item['delay']
        item['delay'] = min(60, item['delay'] * 2)

    def select(self, timeout=1):
        for name, item in self.items.items():
            if item['process'] is None and self.clock() >= item['due']:
                try:
                    proc = subprocess.Popen(item['command'], stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, bufsize=0)
                    os.set_blocking(proc.stdout.fileno(), False)
                    item.update(process=proc, started=self.clock())
                    self.selector.register(proc.stdout, selectors.EVENT_READ, (name, item))
                except OSError:
                    item['due'] = self.clock() + item['delay']
                    item['delay'] = min(60, item['delay'] * 2)
        result = []
        for key, _ in self.selector.select(timeout):
            name, item = key.data
            try:
                raw = os.read(key.fd, 65536)
            except BlockingIOError:
                continue
            if not raw:
                self._retire(item)
                continue
            item['buffer'] += raw
            lines = item['buffer'].split(b'\n')
            item['buffer'] = lines.pop()[-262144:]
            for line in lines:
                result.append((SimpleNamespace(fileobj=io.StringIO(line.decode('utf-8', 'replace')),
                                               data=(name, False, name)), selectors.EVENT_READ))
        return result

    def close(self):
        for item in self.items.values():
            if item['process'] is not None:
                self._retire(item)
        self.selector.close()
