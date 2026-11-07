from typing import Any

from bcsfe import core
from bcsfe.cli import (
    color,
    dialog_creator,
    main,
    file_dialog,
    feature_handler,
    save_management,
    server_cli,
    edits,
    recent_saves,
    color_hex,
    commands,
    prompt,
)


# Core's messages and yes/no questions are shown through the CLI. Looked up at
# call time so a replaced color/prompt function (e.g. in tests) is the one used.
def _show(key: str, **kwargs: Any) -> None:
    color.color_print_key(key, **kwargs)


def _confirm(key: str, **kwargs: Any) -> bool | None:
    return prompt.confirm(key, **kwargs)


core.messages.connect(_show, _confirm)

__all__ = [
    "color",
    "dialog_creator",
    "main",
    "file_dialog",
    "feature_handler",
    "save_management",
    "server_cli",
    "color_hex",
    "edits",
    "recent_saves",
    "commands",
]
