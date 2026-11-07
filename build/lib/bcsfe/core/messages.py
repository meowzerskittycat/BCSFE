"""How core tells the user something, or asks a yes/no question, without
knowing how the user sees it.

Core calls `show` and `confirm` with locale keys. Whatever front end is
running connects them with `connect`; the CLI does so when it is imported.
Until something is connected, messages are logged and questions are
answered "no".
"""

from collections.abc import Callable
from typing import Any

type Show = Callable[..., None]
type Confirm = Callable[..., bool | None]


def _log(key: str, **kwargs: Any) -> None:
    from bcsfe import core

    data = getattr(core, "core_data", None)
    logger = getattr(data, "logger", None)
    if logger is not None:
        logger.log_info(f"{key} {kwargs}" if kwargs else key)


def _no(key: str, **kwargs: Any) -> bool | None:
    return None


_show: Show = _log
_confirm: Confirm = _no


def connect(show: Show, confirm: Confirm) -> None:
    global _show, _confirm
    _show, _confirm = show, confirm


def show(key: str, escape: bool = True, **kwargs: Any) -> None:
    """Show the message for locale key `key`."""
    _show(key, escape=escape, **kwargs)


def confirm(key: str, **kwargs: Any) -> bool | None:
    """Ask the yes/no question for locale key `key`. None means no answer."""
    return _confirm(key, **kwargs)
