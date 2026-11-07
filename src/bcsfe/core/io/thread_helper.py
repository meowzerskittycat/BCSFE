from typing import Any
from collections.abc import Callable, Iterable
import threading


class Thread:
    def __init__(
        self,
        name: str,
        target: Callable[..., Any],
        args: Iterable[Any] | None = None,
    ):
        self.name = name
        self.target = target
        self.args: Iterable[Any] = args if args is not None else []
        self._thread: threading.Thread | None = None

    def start(self):
        self._thread = threading.Thread(
            target=self.target, args=self.args, name=self.name
        )
        self._thread.start()

    def join(self):
        if self._thread is not None:
            self._thread.join()

    def is_alive(self) -> bool:
        if self._thread is not None:
            return self._thread.is_alive()
        return False

    @staticmethod
    def run(name: str, target: Callable[..., None], args: Any):
        thread = Thread(name, target, args)
        thread.start()
        return thread
