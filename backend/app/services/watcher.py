import logging
import threading
import time

from . import scanner


class LibraryWatcher:
    def __init__(self, interval_sec: int):
        self.interval_sec = interval_sec
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="library-watcher", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        while not self._stop.is_set():
            try:
                scanner.scan_library()
            except Exception:
                logging.getLogger(__name__).exception("Background scan failed")
            self._stop.wait(self.interval_sec)