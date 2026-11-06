"""Shared model for stage-progress sections: maps, each with stars (crowns),
each with stages.

The save stores these sections column by column rather than map by map:
first the selected stage of every star of every map, then the clear
progress of every star, then the stage clear counts, then the unlock
states. Each section uses different integer widths and headers, but the
model and the editing logic are the same, so they live here once and each
section (main chapters, gauntlets, legend quest, aku, events) only
describes its own layout.
"""

from collections.abc import Iterable
from typing import Any, cast

from bcsfe.core.io.data import Data
from bcsfe.core.io.schema import Codec


class Stage:
    def __init__(self, clear_times: int = 0, tries: int | None = None):
        self.clear_times = clear_times
        # Only legend quest stages record how many attempts were made.
        self.tries = tries

    def clear_stage(self, clear_amount: int = 1, ensure_cleared_only: bool = False):
        if ensure_cleared_only:
            self.clear_times = self.clear_times or clear_amount
            if self.tries is not None:
                self.tries = self.tries or clear_amount
        else:
            self.clear_times = clear_amount
            if self.tries is not None:
                self.tries = clear_amount

    def unclear_stage(self):
        self.clear_times = 0
        if self.tries is not None:
            self.tries = 0

    def to_json(self) -> Any:
        if self.tries is None:
            return self.clear_times
        return {"clear_times": self.clear_times, "tries": self.tries}

    @staticmethod
    def from_json(data: Any) -> Stage:
        if isinstance(data, dict):
            d = cast(dict[str, int], data)
            return Stage(d.get("clear_times", 0), d.get("tries", 0))
        return Stage(int(data))

    def __repr__(self) -> str:
        if self.tries is None:
            return f"Stage({self.clear_times})"
        return f"Stage({self.clear_times}, tries={self.tries})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Stage)
            and self.clear_times == other.clear_times
            and self.tries == other.tries
        )


class Star:
    """One star (crown) of a map: its stages and how far through it you are."""

    def __init__(self, selected_stage: int = 0, total_stages: int = 0):
        self.selected_stage = selected_stage
        self.clear_progress = 0
        self.stages = [Stage() for _ in range(total_stages)]
        self.chapter_unlock_state = 0
        # Real stage count of the map when known (the stored list is padded
        # to the longest map); 0 means "use the stored length".
        self.total_stages = 0

    def last_stage(self) -> int:
        return (self.total_stages or len(self.stages)) - 1

    def clear_stage(
        self,
        index: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        """Clear one stage. Returns True if it was the last stage of the star."""
        if overwrite_clear_progress:
            self.clear_progress = index + 1
        else:
            self.clear_progress = max(self.clear_progress, index + 1)
        self.chapter_unlock_state = 3
        self.stages[index].clear_stage(clear_amount, ensure_cleared_only)
        return index == self.last_stage()

    def unclear_stage(self, index: int) -> bool:
        self.clear_progress = min(self.clear_progress, index)
        self.stages[index].unclear_stage()
        return True

    def clear_map(self, increment: bool = True) -> bool:
        """Clear every stage, adding a clear (or making sure there is one)."""
        self.clear_progress = len(self.stages)
        self.chapter_unlock_state = 3
        for stage in self.stages:
            stage.clear_stage(
                stage.clear_times + 1 if increment else stage.clear_times or 1
            )
        return True

    def to_json(self, selected_key: str = "selected_stage") -> dict[str, Any]:
        return {
            selected_key: self.selected_stage,
            "clear_progress": self.clear_progress,
            "stages": [stage.to_json() for stage in self.stages],
            "chapter_unlock_state": self.chapter_unlock_state,
        }

    @staticmethod
    def from_json(data: dict[str, Any], selected_key: str = "selected_stage") -> Star:
        star = Star(data.get(selected_key, 0))
        star.clear_progress = data.get("clear_progress", 0)
        star.stages = [Stage.from_json(stage) for stage in data.get("stages", [])]
        star.chapter_unlock_state = data.get("chapter_unlock_state", 0)
        return star

    def __repr__(self) -> str:
        return (
            f"Star({self.selected_stage}, {self.clear_progress}, "
            f"{self.stages}, {self.chapter_unlock_state})"
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Star)
            and self.selected_stage == other.selected_stage
            and self.clear_progress == other.clear_progress
            and self.stages == other.stages
            and self.chapter_unlock_state == other.chapter_unlock_state
        )


class MapStars:
    """One map: a star list. (Named `chapters` for compatibility.)"""

    def __init__(self, chapters: list[Star]):
        self.chapters = chapters
        # Only event maps store this.
        self.legend_restriction = 0

    @staticmethod
    def new(total_stars: int, total_stages: int = 0) -> MapStars:
        return MapStars([Star(0, total_stages) for _ in range(total_stars)])

    def clear_stage(
        self,
        star: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        finished = self.chapters[star].clear_stage(
            stage, clear_amount, overwrite_clear_progress, ensure_cleared_only
        )
        if finished and star + 1 < len(self.chapters):
            self.chapters[star + 1].chapter_unlock_state = 1
        return finished

    def unclear_stage(self, star: int, stage: int) -> bool:
        finished = self.chapters[star].unclear_stage(stage)
        if finished:
            for later in self.chapters[star + 1 :]:
                later.chapter_unlock_state = 0
        return finished

    def clear_map(self, star: int, increment: bool = True) -> bool:
        finished = self.chapters[star].clear_map(increment)
        if finished and star + 1 < len(self.chapters):
            self.chapters[star + 1].chapter_unlock_state = 1
        return finished

    def clear_chapter(self, increment: bool = True) -> bool:
        for star in self.chapters:
            star.clear_map(increment)
        return True

    def to_json(self, selected_key: str = "selected_stage") -> list[dict[str, Any]]:
        return [star.to_json(selected_key) for star in self.chapters]

    @staticmethod
    def from_json(
        data: list[dict[str, Any]], selected_key: str = "selected_stage"
    ) -> MapStars:
        return MapStars([Star.from_json(star, selected_key) for star in data])

    def __repr__(self) -> str:
        return f"MapStars({self.chapters})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, MapStars)
            and self.chapters == other.chapters
            and self.legend_restriction == other.legend_restriction
        )


class Maps:
    """Behaviour shared by every section that is a list of maps."""

    chapters: list[MapStars]

    def clear_stage(
        self,
        map: int,
        star: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        finished = self.chapters[map].clear_stage(
            star, stage, clear_amount, overwrite_clear_progress, ensure_cleared_only
        )
        if finished and map + 1 < len(self.chapters):
            self.chapters[map + 1].chapters[0].chapter_unlock_state = 1
        return finished

    def unclear_stage(self, map: int, star: int, stage: int) -> bool:
        finished = self.chapters[map].unclear_stage(star, stage)
        if finished and map + 1 < len(self.chapters) and star == 0:
            for later in self.chapters[map + 1].chapters:
                later.chapter_unlock_state = 0
        return finished

    def clear_map(self, map: int, star: int, increment: bool = True):
        if self.chapters[map].clear_map(star, increment) and map + 1 < len(
            self.chapters
        ):
            self.chapters[map + 1].chapters[0].chapter_unlock_state = 1

    def clear_chapter(self, map: int, increment: bool = True):
        if self.chapters[map].clear_chapter(increment) and map + 1 < len(self.chapters):
            self.chapters[map + 1].chapters[0].chapter_unlock_state = 1

    def clear_group(self, increment: bool = True):
        for map in self.chapters:
            map.clear_chapter(increment)

    def get_total_stars(self, map: int) -> int:
        try:
            return len(self.chapters[map].chapters)
        except IndexError:
            return 0

    def get_total_stages(self, map: int, star: int) -> int:
        try:
            return len(self.chapters[map].chapters[star].stages)
        except IndexError:
            return 0

    def set_total_stages(self, map: int, total_stages: int):
        for star in self.chapters[map].chapters:
            star.total_stages = total_stages

    def unclear_rest(self, stages: list[int], stars: int, id: int):
        """Unclear every stage from max(stages) on, in star `stars` and later."""
        if not stages:
            return
        for star in range(stars, self.get_total_stars(id)):
            for stage in range(max(stages), self.get_total_stages(id, star)):
                self.chapters[id].chapters[star].stages[stage].clear_times = 0
                self.chapters[id].chapters[star].clear_progress = 0

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and vars(self) == vars(other)


# --- reading and writing columns -------------------------------------------


def dims(maps: list[MapStars]) -> tuple[int, int, int]:
    """(maps, stages per star, stars per map); every map has the same shape."""
    stars = len(maps[0].chapters) if maps else 0
    stages = len(maps[0].chapters[0].stages) if maps and maps[0].chapters else 0
    return len(maps), stages, stars


def read_selected(
    data: Data, total_maps: int, total_stars: int, codec: Codec[int]
) -> list[MapStars]:
    """The first column also creates the maps and stars."""
    return [
        MapStars([Star(codec.read(data)) for _ in range(total_stars)])
        for _ in range(total_maps)
    ]


def write_selected(data: Data, maps: Iterable[MapStars], codec: Codec[int]):
    write_column(data, maps, "selected_stage", codec)


def read_column(data: Data, maps: Iterable[MapStars], attr: str, codec: Codec[int]):
    for map in maps:
        for star in map.chapters:
            setattr(star, attr, codec.read(data))


def write_column(data: Data, maps: Iterable[MapStars], attr: str, codec: Codec[int]):
    for map in maps:
        for star in map.chapters:
            codec.write(data, getattr(star, attr))


def read_stages(
    data: Data,
    maps: Iterable[MapStars],
    total_stages: int,
    codec: Codec[int],
    *,
    interleaved: bool = True,
    tries: Codec[int] | None = None,
):
    """Stage clear counts, map by map.

    Interleaved: stage 0 of every star, then stage 1 of every star, ...
    Otherwise all stages of star 0, then of star 1, ...
    With `tries` (legend quest), each map's attempt counts follow its clear
    counts, laid out the same way.
    """
    for map in maps:
        if interleaved:
            for _ in range(total_stages):
                for star in map.chapters:
                    star.stages.append(Stage(codec.read(data)))
        else:
            for star in map.chapters:
                star.stages = [Stage(codec.read(data)) for _ in range(total_stages)]
        if tries is not None:
            for i in range(total_stages):
                for star in map.chapters:
                    star.stages[i].tries = tries.read(data)


def write_stages(
    data: Data,
    maps: Iterable[MapStars],
    codec: Codec[int],
    *,
    interleaved: bool = True,
    tries: Codec[int] | None = None,
):
    for map in maps:
        if interleaved:
            if not map.chapters:
                continue
            for i in range(len(map.chapters[0].stages)):
                for star in map.chapters:
                    codec.write(data, star.stages[i].clear_times)
        else:
            for star in map.chapters:
                for stage in star.stages:
                    codec.write(data, stage.clear_times)
        if tries is not None and map.chapters:
            for i in range(len(map.chapters[0].stages)):
                for star in map.chapters:
                    tries.write(data, star.stages[i].tries or 0)
