"""Download the game data the tests run the menu with, into tests/game_data/.

The tests find it there and use it; without it, they check that every menu
copes with no game data instead. CI runs this before the tests (and caches
the result). The folder is gitignored: game data isn't committed.

    python tests/tools/get_game_data.py

Needs only the standard library.
"""

import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

# The region and version the tests use. Keep it to one the real fixture save
# (tests/fixtures/real/) can use, and change CI's cache key if you change it.
REGION = "en"
VERSION = "15.6.1"
SOURCES = [
    "https://raw.githubusercontent.com/meowzerskittycat/bcdata/main/metadata.json",
    "https://git.battlecatsmodding.org/fieryhenry/BCData/raw/branch/main/metadata.json",
    "https://gitlab.com/fieryhenry/bcdata/-/raw/main/metadata.json",
]
OUT = Path(__file__).resolve().parent.parent / "game_data"
MAX_SIZE = 50 * 1024 * 1024


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "bcsfe-tests"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError(f"{url} is larger than {MAX_SIZE} bytes")
    return data


def main() -> int:
    target = OUT / REGION / VERSION
    if (target / "downloaded").exists():
        print(f"already have {REGION} {VERSION} in {target}")
        return 0
    for source in SOURCES:
        try:
            metadata = json.loads(fetch(source))
            url = metadata["base_url"] + metadata["versions"][REGION][VERSION]
            archive = fetch(url)
            target.mkdir(parents=True, exist_ok=True)
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tar:
                tar.extractall(target, filter="data")
        except Exception as e:  # try the next source
            print(f"skipping {source}: {e}")
            continue
        (target / "downloaded").touch()
        print(f"downloaded {REGION} {VERSION} from {url}")
        return 0
    print("no source had the game data")
    return 1


if __name__ == "__main__":
    sys.exit(main())
