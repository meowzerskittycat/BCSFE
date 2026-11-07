"""Game data comes from the first source that answers, and a download falls
back to another source when one fails. No network: requests are faked."""

import io
import tarfile
from collections.abc import Iterator
from typing import Any

import pytest

from bcsfe import core
from bcsfe.core.server import game_data_getter
from bcsfe.core.server.game_data_getter import SOURCES, GameDataGetter


class Response:
    def __init__(self, status_code: int, body: Any = None, content: bytes = b""):
        self.status_code = status_code
        self.body = body
        self.content = content

    def json(self) -> Any:
        return self.body


def archive() -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:xz") as tar:
        data = b"hello"
        info = tarfile.TarInfo("DataLocal/test.csv")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return out.getvalue()


def metadata(base: str) -> dict[str, Any]:
    return {"base_url": base, "versions": {"en": {"15.6.1": "en-15.6.1.tar.xz"}}}


class Web:
    """Fake responses by URL; any other URL is unreachable."""

    def __init__(self) -> None:
        self.pages: dict[str, Response] = {}
        self.requested: list[str] = []
        self.shown: list[str] = []

    def __setitem__(self, url: str, response: Response) -> None:
        self.pages[url] = response


@pytest.fixture
def web(monkeypatch: pytest.MonkeyPatch) -> Iterator[Web]:
    fake = Web()

    def get(self: core.RequestHandler, *_a: Any, **_k: Any) -> Response | None:
        fake.requested.append(self.url)
        return fake.pages.get(self.url)

    monkeypatch.setattr(core.RequestHandler, "get", get)
    monkeypatch.setattr(
        game_data_getter.messages, "show", lambda key, **_k: fake.shown.append(key)
    )
    monkeypatch.setattr(GameDataGetter, "_metadata", {})
    monkeypatch.setattr(GameDataGetter, "_reported_unreachable", False)
    monkeypatch.setattr(
        GameDataGetter, "get_all_downloaded_versions", staticmethod(lambda: {})
    )
    yield fake


def getter() -> GameDataGetter:
    return GameDataGetter(
        core.CountryCode.from_code("en"),
        core.GameVersion.from_string("15.6.1"),
        do_print=False,
    )


def test_the_configured_source_is_tried_first() -> None:
    assert GameDataGetter.sources()[0] == GameDataGetter.repo_url()
    assert sorted(set(GameDataGetter.sources())) == sorted(SOURCES)


def test_a_source_that_is_down_is_skipped_without_asking(web: Web) -> None:
    web[SOURCES[1]] = Response(200, metadata("https://second/"))
    assert GameDataGetter.get_metadata() == metadata("https://second/")
    assert web.shown == []


def test_a_broken_answer_counts_as_down(web: Web) -> None:
    web[SOURCES[0]] = Response(404, "Not found")
    web[SOURCES[1]] = Response(200, ["not", "metadata"])
    web[SOURCES[2]] = Response(200, metadata("https://mirror/"))
    assert GameDataGetter.get_metadata() == metadata("https://mirror/")


def test_no_source_answering_is_reported_once(web: Web) -> None:
    assert GameDataGetter.get_metadata() is None
    assert GameDataGetter.get_metadata() is None
    assert web.shown == ["game_data_unreachable"]


def test_metadata_is_fetched_once_per_session(web: Web) -> None:
    web[SOURCES[0]] = Response(200, metadata("https://first/"))
    GameDataGetter.get_metadata()
    GameDataGetter.get_metadata()
    assert web.requested.count(SOURCES[0]) == 1


def test_a_failed_download_falls_back_to_another_source(web: Web) -> None:
    web[SOURCES[0]] = Response(200, metadata("https://first/"))
    web[SOURCES[2]] = Response(200, metadata("https://mirror/"))
    web["https://first/en-15.6.1.tar.xz"] = Response(200, content=b"not an archive")
    web["https://mirror/en-15.6.1.tar.xz"] = Response(200, content=archive())

    g = getter()
    assert g.download_version_data() is True
    path = g.get_version_path()
    assert path is not None
    assert path.add("DataLocal").add("test.csv").read().data == b"hello"


def test_a_download_no_source_has_is_reported(web: Web) -> None:
    web[SOURCES[0]] = Response(200, metadata("https://first/"))
    g = getter()
    g.print = True
    assert g.download_version_data() is None
    assert web.shown[-1] == "game_data_download_failed"


def gv(version: str) -> core.GameVersion:
    return core.GameVersion.from_string(version)


@pytest.mark.parametrize(
    ("save", "expected"),
    [
        ("15.6.1", "15.6.1"),  # the same version
        ("15.6.0", "15.6.1"),  # else the oldest newer one
        ("15.11.0", "15.11.0"),
        ("15.9.5", "15.10.0"),  # 15.10 is newer than 15.9, not older
        ("16.0.0", "15.11.0"),  # else the newest older one
    ],
)
def test_the_closest_game_data_version_is_chosen(save: str, expected: str) -> None:
    available = ["15.10.0", "15.6.1", "15.11.0", "9.0.0", "15.9.0"]
    assert GameDataGetter.choose_version(available, gv(save)) == expected


def test_no_usable_version_is_none() -> None:
    assert GameDataGetter.choose_version([], gv("15.6.1")) is None
    assert GameDataGetter.choose_version(["not a version"], gv("15.6.1")) is None


def test_offline_an_older_downloaded_version_is_used(
    web: Web, monkeypatch: pytest.MonkeyPatch
) -> None:
    en = core.CountryCode.from_code("en")
    monkeypatch.setattr(
        GameDataGetter,
        "get_all_downloaded_versions",
        staticmethod(lambda: {en: [gv("15.5.0"), gv("15.6.1")]}),
    )
    g = GameDataGetter(en, gv("15.7.0"), do_print=False)
    assert g.version == "15.6.1"
