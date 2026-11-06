"""Run every menu feature with typed answers and check none of them crash.

Each feature gets a cycle of plausible answers (numbers, yes/no, ranges,
"all") until it has had enough, at which point the next prompt raises
KeyboardInterrupt, as Ctrl+C would. Whatever the feature did must leave a
save that writes and reads back identically.

There's no game data and no network here, so features that need either
must fail gracefully rather than crash.
"""

import itertools
from collections.abc import Iterator

import pytest
import requests

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.feature_handler import FeatureHandler

from .conftest import real_fixtures

# Save management uploads, writes files and exits; it's tested separately.
SKIP_CATEGORIES = {"save_management"}
SKIP_FEATURES = {"exit"}

ANSWERS = {
    "ones": ["1"],
    "mixed": ["1", "y", "5", "1 2", "n", "2"],
    "all": ["2", "y", "100", "all", "1", "n"],
}
MAX_ANSWERS = 60


def save_bytes() -> bytes:
    return real_fixtures()[0].read_bytes()


def features() -> list[tuple[str, ...]]:
    handler = FeatureHandler(core.SaveFile(core.Data(save_bytes())))
    return [
        path
        for path in handler.all_features()
        if path[0] not in SKIP_CATEGORIES and path[-1] not in SKIP_FEATURES
    ]


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise requests.exceptions.ConnectionError("network is off in tests")

    monkeypatch.setattr(requests, "get", blocked)
    monkeypatch.setattr(requests, "post", blocked)


def test_every_feature_is_tested() -> None:
    assert len(features()) > 80


@pytest.mark.parametrize("answers", ANSWERS.values(), ids=ANSWERS.keys())
@pytest.mark.parametrize("path", features(), ids="/".join)
def test_feature_does_not_crash(
    monkeypatch: pytest.MonkeyPatch, path: tuple[str, ...], answers: list[str]
) -> None:
    save = core.SaveFile(core.Data(save_bytes()))
    feature = FeatureHandler(save).get_feature(path)

    typed: Iterator[str] = itertools.islice(itertools.cycle(answers), MAX_ANSWERS)

    def answer(*_args: object, **_kwargs: object) -> str:
        try:
            return next(typed)
        except StopIteration:
            raise KeyboardInterrupt from None

    monkeypatch.setattr(color, "color_input", answer)
    try:
        feature(save)
    except KeyboardInterrupt:
        pass

    written = save.to_data().to_bytes()
    reloaded = core.SaveFile(core.Data(written))
    assert reloaded.to_data().to_bytes() == written
