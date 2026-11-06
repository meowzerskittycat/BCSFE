"""The layout of the main save file, declared once.

`SaveFile` used to list its ~400 fields five times by hand: when reading,
when writing, for JSON export, for JSON import and for new saves. Here each
field is declared once, in the order it's stored, with the game versions
and regions it's stored for. Reading, writing, JSON and new saves are all
driven from this list (see `run_read`, `run_write`, `to_json`, `from_json`
and `init_values`).

A field can appear more than once when the game stores it in different
places or with different lengths depending on the version or region; only
the entries whose condition holds are read and written, and JSON has the
field once.

Sections (cats, gatya, story...) are their own classes. Some are stored in
several places in the save, so a section is created by its `Sec` entry and
its other pieces are read and written by `Part` entries.
"""

import base64
import datetime
import functools
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from bcsfe import core
from bcsfe.core.io.data import Data
from bcsfe.core.io.schema import (
    F64,
    I8,
    I16,
    I32,
    I64,
    Array,
    Bool,
    Codec,
    Map,
    String,
    Tuple as ListTuple,
)

if TYPE_CHECKING:
    from bcsfe.core.io.save import SaveFile

type Cond = Callable[[SaveFile], bool]

_EPOCH = datetime.datetime(1970, 1, 1)


def to_timestamp(date: datetime.datetime) -> float:
    """date.timestamp(), but also works for dates around 1970 on Windows,
    where the C library rejects local times before the epoch."""
    try:
        return date.timestamp()
    except OSError, OverflowError, ValueError:
        return (date - _EPOCH).total_seconds() + time.timezone


def from_timestamp(timestamp: float) -> datetime.datetime:
    """Inverse of to_timestamp (local time, like datetime.fromtimestamp)."""
    try:
        return datetime.datetime.fromtimestamp(timestamp)
    except OSError, OverflowError, ValueError:
        return _EPOCH + datetime.timedelta(seconds=timestamp - time.timezone)


# --- codecs only the main save needs -------------------------------------


class DateCodec(Codec[datetime.datetime]):
    """Six int32s (year, month, day, hour, minute, second); a timestamp in JSON."""

    def read(self, data: Data, gv: Any = None) -> datetime.datetime:
        return data.read_date()

    def write(self, data: Data, value: datetime.datetime, gv: Any = None) -> None:
        data.write_date(value)

    def default(self) -> datetime.datetime:
        return from_timestamp(0)

    def to_json(self, value: datetime.datetime) -> Any:
        return to_timestamp(value)

    def from_json(self, value: Any) -> datetime.datetime:
        return from_timestamp(value)


class RestCodec(Codec[bytes]):
    """Everything up to the 32-byte hash at the end; base64 in JSON."""

    def read(self, data: Data, gv: Any = None) -> bytes:
        return data.read_to_end(32)

    def write(self, data: Data, value: bytes, gv: Any = None) -> None:
        data.write_bytes(value)

    def default(self) -> bytes:
        return b""

    def to_json(self, value: bytes) -> Any:
        return base64.b64encode(value).decode("utf-8")

    def from_json(self, value: Any) -> bytes:
        return base64.b64decode(value)


class Tuple(ListTuple):
    """A tuple kept as a tuple in the JSON dict (it is still written as a list).

    The old hand-written `to_dict` returned these values as they were stored,
    so tools that walk the dict's lists, like the fixture generator, skip them.
    """

    def to_json(self, value: tuple[Any, ...]) -> Any:
        return tuple(super().to_json(value))


class Uil10Codec(Codec[tuple[Any, ...]]):
    """An entry of `uil10`; the string is only stored from 14.5."""

    BEFORE = Tuple(I32, I32, Bool, Bool, Bool, I32, I32, I32, Bool, Bool, Bool)

    def read(self, data: Data, gv: Any = None) -> tuple[Any, ...]:
        start = self.BEFORE.read(data, gv)
        text = data.read_string() if gv >= 140500 else None
        return (*start, text, data.read_bool())

    def write(self, data: Data, value: tuple[Any, ...], gv: Any = None) -> None:
        self.BEFORE.write(data, tuple(value[:11]), gv)
        if gv >= 140500:
            data.write_string(value[11] or "")
        data.write_bool(value[12])

    def default(self) -> tuple[Any, ...]:
        return (*self.BEFORE.default(), None, False)

    def to_json(self, value: tuple[Any, ...]) -> Any:
        return tuple(value)

    def from_json(self, value: Any) -> tuple[Any, ...]:
        start = self.BEFORE.from_json(value[:11])
        return (*start, value[11], bool(value[12]))


class PaddedTuple(Tuple):
    """A tuple whose missing trailing values are written as 0."""

    def write(self, data: Data, value: tuple[Any, ...], gv: Any = None) -> None:
        values = list(value)[: len(self.items)]
        values += [0] * (len(self.items) - len(values))
        super().write(data, tuple(values), gv)


Date = DateCodec()
Rest = RestCodec()
Ints = Array(I32)
Bools = Array(Bool)
Strings = Array(String)
Shorts = Array(I16, I16)


# --- layout entries -------------------------------------------------------


def always(_: SaveFile) -> bool:
    return True


@dataclass
class F:
    """A field: `name` on the save, stored with `codec`.

    `key` is its JSON name when that differs. `binary=False` fields aren't
    stored by themselves (they're part of a `Raw` entry) but are in JSON.
    """

    name: str
    codec: Codec[Any]
    when: Cond = always
    key: str | None = None
    binary: bool = True

    @property
    def json_key(self) -> str:
        return self.key or self.name


@dataclass
class Sec:
    """A section object, created where its first piece is stored."""

    name: str
    cls: Any
    read: Callable[[Data, SaveFile], Any]
    write: Callable[[Any, Data, SaveFile], None]
    init: Callable[[SaveFile], Any]
    when: Cond = always

    @property
    def json_key(self) -> str:
        return self.name


@dataclass
class Part:
    """Another piece of an already-created section."""

    name: str
    read: Callable[[Any, Data, SaveFile], None]
    write: Callable[[Any, Data, SaveFile], None]
    when: Cond = always


@dataclass
class Expect:
    """A marker int the game writes after each block of fields."""

    value: int
    when: Cond = always


@dataclass
class Dst:
    """A daylight-saving flag (only stored outside Japan from 4.9)."""

    when: Cond = always


@dataclass
class Raw:
    """Fields stored in an unusual order; they're declared separately with
    `binary=False` so JSON and new saves still know about them."""

    read: Callable[[Data, SaveFile], None]
    write: Callable[[Data, SaveFile], None]
    when: Cond = always


type Entry = F | Sec | Part | Expect | Dst | Raw


def ge(version: int) -> Cond:
    return lambda s: s.game_version >= version


def lt(version: int) -> Cond:
    return lambda s: s.game_version < version


def between(low: int, high: int) -> Cond:
    """low <= game version <= high."""
    return lambda s: low <= s.game_version <= high


def jp(s: SaveFile) -> bool:
    return s.is_jp()


def not_jp(s: SaveFile) -> bool:
    return s.not_jp()


def both(a: Cond, b: Cond) -> Cond:
    return lambda s: a(s) and b(s)


def group(when: Cond, *entries: Entry | list[Entry]) -> list[Entry]:
    """`entries`, each only stored when `when` (and its own condition) holds."""
    out: list[Entry] = []
    for entry in entries:
        for e in entry if isinstance(entry, list) else [entry]:
            e.when = both(when, e.when) if e.when is not always else when
            out.append(e)
    return out


def sec(
    name: str,
    cls: Any,
    *,
    gv_read: bool = False,
    gv_init: bool = False,
    when: Cond = always,
) -> Sec:
    """A section with plain `read`/`write`/`init` methods."""
    if gv_read:
        read: Callable[[Data, SaveFile], Any] = lambda d, s: cls.read(d, s.game_version)
        write: Callable[[Any, Data, SaveFile], None] = lambda o, d, s: o.write(
            d, s.game_version
        )
    else:
        read = lambda d, s: cls.read(d)
        write = lambda o, d, s: o.write(d)
    init: Callable[[SaveFile], Any] = (
        (lambda s: cls.init(s.game_version)) if gv_init else (lambda s: cls.init())
    )
    return Sec(name, cls, read, write, init, when)


def part(name: str, method: str, *, gv: bool = False, when: Cond = always) -> Part:
    """`read_<method>` / `write_<method>` on the section called `name`."""

    def read(o: Any, d: Data, s: SaveFile) -> None:
        f = getattr(o, f"read_{method}")
        f(d, s.game_version) if gv else f(d)

    def write(o: Any, d: Data, s: SaveFile) -> None:
        f = getattr(o, f"write_{method}")
        f(d, s.game_version) if gv else f(d)

    return Part(name, read, write, when)


def named_part(name: str, piece: str, *, gv: bool = False) -> Part:
    """`read_part(piece)` / `write_part(piece)` on a schema section."""

    def read(o: Any, d: Data, s: SaveFile) -> None:
        o.read_part(d, piece, s.game_version) if gv else o.read_part(d, piece)

    def write(o: Any, d: Data, s: SaveFile) -> None:
        o.write_part(d, piece, s.game_version) if gv else o.write_part(d, piece)

    return Part(name, read, write)


def ints(*names: str) -> list[Entry]:
    return [F(n, I32) for n in names]


def bools(*names: str) -> list[Entry]:
    return [F(n, Bool) for n in names]


def doubles(*names: str) -> list[Entry]:
    return [F(n, F64) for n in names]


def bytes_(*names: str) -> list[Entry]:
    return [F(n, I8) for n in names]


def shorts(*names: str) -> list[Entry]:
    return [F(n, I16) for n in names]


# The first fields mix the save time with other values.


def _read_header_time(d: Data, s: SaveFile) -> None:
    year = d.read_int()
    s.year = d.read_int()
    month = d.read_int()
    s.month = d.read_int()
    day = d.read_int()
    s.day = d.read_int()
    s.timestamp = d.read_double()
    hour = d.read_int()
    minute = d.read_int()
    second = d.read_int()
    s.read_dst()
    s.date = datetime.datetime(year, month, day, hour, minute, second)


def _write_header_time(d: Data, s: SaveFile) -> None:
    d.write_int(s.date.year)
    d.write_int(s.year)
    d.write_int(s.date.month)
    d.write_int(s.month)
    d.write_int(s.date.day)
    d.write_int(s.day)
    d.write_double(s.timestamp)
    d.write_int(s.date.hour)
    d.write_int(s.date.minute)
    d.write_int(s.date.second)
    s.write_dst()


def _cats(method: str, gv: bool = True) -> Part:
    return part("cats", method, gv=gv)


def _build() -> list[Entry]:
    c = core
    L: list[Entry] = [
        F("dsts", Bools, binary=False),
        F("ub1", Bool, when=lambda s: s.game_version >= 10 or s.not_jp()),
        *bools("mute_bgm", "mute_se"),
        *ints("catfood", "current_energy"),
        F("year", I32, binary=False),
        F("month", I32, binary=False),
        F("day", I32, binary=False),
        F("timestamp", F64, binary=False),
        F("date", Date, binary=False),
        Raw(_read_header_time, _write_header_time),
        *ints(
            "ui1", "stamp_value_save", "ui2", "upgrade_state", "xp", "tutorial_state"
        ),
        *ints("ui3", "koreaSuperiorTreasureState"),
        F("unlock_popups_11", Array(I32, 3)),
        *ints("ui5", "unlock_enemy_guide", "ui6"),
        F("ub0", Bool),
        *ints("ui7", "cleared_eoc_1", "ui8", "unlocked_ending"),
        sec("lineups", c.LineUps, gv_read=True, gv_init=True),
        sec("stamp_data", c.StampData),
        sec("story", c.StoryChapters),
        F("enemy_guide", Array(I32, 231), when=between(20, 25)),
        F("enemy_guide", Ints, when=lambda s: not 20 <= s.game_version <= 25),
        Sec(
            "cats",
            c.Cats,
            lambda d, s: c.Cats.read_unlocked(d, s.game_version),
            lambda o, d, s: o.write_unlocked(d, s.game_version),
            lambda s: c.Cats.init(s.game_version),
        ),
        _cats("upgrade"),
        _cats("current_form"),
        Sec(
            "special_skills",
            c.SpecialSkills,
            lambda d, s: c.SpecialSkills.read_upgrades(d),
            lambda o, d, s: o.write_upgrades(d),
            lambda s: c.SpecialSkills.init(),
        ),
        F("menu_unlocks", Array(I32, 5), when=lambda s: s.game_version <= 25),
        F("unlock_popups_0", Array(I32, 5), when=lambda s: s.game_version <= 25),
        F("menu_unlocks", Array(I32, 6), when=between(26, 26)),
        F("unlock_popups_0", Array(I32, 6), when=between(26, 26)),
        F("menu_unlocks", Ints, when=ge(27)),
        F("unlock_popups_0", Ints, when=ge(27)),
        Sec(
            "battle_items",
            c.BattleItems,
            lambda d, s: c.BattleItems.read_items(d),
            lambda o, d, s: o.write_items(d),
            lambda s: c.BattleItems.init(),
        ),
        F("new_dialogs_2", Array(I32, 17), when=lambda s: s.game_version <= 26),
        F("new_dialogs_2", Ints, when=ge(27)),
        F("uil1", Array(I32, 20)),
        F("moneko_bonus", Array(I32, 1)),
        F("daily_reward_initialized", Array(I32, 1)),
        part("battle_items", "locked_items"),
        Dst(),
        F("date_2", Date),
        part("story", "treasure_festival"),
        Dst(),
        F("date_3", Date),
        F("ui0", I32, when=lambda s: s.game_version <= 37),
        *ints(
            "stage_unlock_cat_value", "show_ending_value", "chapter_clear_cat_unlock"
        ),
        *ints("ui9", "ios_android_month", "ui10"),
        F("save_data_4_hash", String),
        Sec(
            "mysale",
            c.MySale,
            lambda d, s: c.MySale.read_bonus_hash(d),
            lambda o, d, s: o.write_bonus_hash(d),
            lambda s: c.MySale.init(),
        ),
        F("chara_flags", Array(I32, 2)),
        *group(lambda s: s.game_version <= 37, F("uim1", I32), F("ubm1", Bool)),
        F("chara_flags_2", Array(I32, 2)),
        *ints("normal_tickets", "rare_tickets"),
        _cats("gatya_seen"),
        part("special_skills", "gatya_seen"),
        _cats("storage"),
        sec("event_stages", c.EventChapters, gv_read=True, gv_init=True),
        *ints("itf1_ending", "continue_flag"),
        F("unlock_popups_8", Array(I32, 36), when=ge(20)),
        F("unit_drops", Array(I32, 110), when=between(20, 25)),
        F("unit_drops", Ints, when=ge(26)),
        Sec(
            "gatya",
            c.Gatya,
            lambda d, s: c.Gatya.read_rare_normal_seed(d, s.game_version),
            lambda o, d, s: o.write_rare_normal_seed(d),
            lambda s: c.Gatya.init(),
        ),
        F("get_event_data", Bool),
        F("achievements", Array(Bool, 7)),
        F("os_value", I32),
        Dst(),
        F("date_4", Date),
        Part(
            "gatya",
            lambda o, d, s: o.read2(d),
            lambda o, d, s: o.write2(d),
        ),
        F("player_id", String, when=not_jp),
        F("order_ids", Strings),
        *group(
            not_jp,
            doubles("g_timestamp", "g_servertimestamp", "m_gettimesave"),
            F("usl1", Strings),
            F("energy_notification", Bool),
            F("full_gameversion", I32),
        ),
        part("lineups", "2", gv=True),
        part("event_stages", "legend_restrictions", gv=True),
        *group(
            lambda s: s.game_version <= 37,
            F("uil2", Array(I32, 7)),
            F("uil3", Array(I32, 7)),
            F("uil4", Array(I32, 7)),
        ),
        *doubles("g_timestamp_2", "g_servertimestamp_2", "m_gettimesave_2"),
        F("unknown_timestamp", F64),
        part("gatya", "trade_progress"),
        F("usl2", Strings, when=lambda s: s.game_version <= 37),
        F("m_dGetTimeSave2", F64, when=not_jp),
        F("ui11", I32, when=jp),
        F("ubl1", Array(Bool, 12), when=between(20, 25)),
        F("ubl1", Bools, when=lambda s: 26 <= s.game_version < 39),
        _cats("max_upgrade_levels"),
        part("special_skills", "max_upgrade_levels"),
        sec("user_rank_rewards", c.UserRankRewards, gv_read=True, gv_init=True),
        F("m_dGetTimeSave2", F64, when=jp),
        _cats("unlocked_forms"),
        F("transfer_code", String),
        F("confirmation_code", String),
        F("transfer_flag", Bool),
        *group(
            ge(20),
            sec("item_reward_stages", c.ItemRewardChapters, gv_read=True, gv_init=True),
            sec("timed_score_stages", c.TimedScoreChapters, gv_read=True, gv_init=True),
            F("inquiry_code", String),
            sec("officer_pass", c.OfficerPass),
            F("has_account", I8),
            F("backup_state", I32),
            F("ub2", Bool, when=not_jp),
            Expect(44),
            F("itf1_complete", I32),
            part("story", "itf_timed_scores"),
            F("title_chapter_bg", I32),
            F("combo_unlocks", Ints, when=ge(27)),
            F("combo_unlocked_10k_ur", Bool),
            Expect(45),
        ),
        *group(
            ge(21),
            Expect(46),
            Part(
                "gatya",
                lambda o, d, s: o.read_event_seed(d, s.game_version),
                lambda o, d, s: o.write_event_seed(d),
            ),
            F("event_capsules", Array(I32, 100), when=lt(34)),
            F("event_capsules_counter", Array(I32, 100), when=lt(34)),
            F("event_capsules", Ints, when=ge(34)),
            F("event_capsules_counter", Ints, when=ge(34)),
            Expect(47),
        ),
        Expect(48, when=ge(22)),
        *group(
            ge(23),
            F("energy_notification", Bool, when=jp),
            F("m_dGetTimeSave3", F64),
            F("gatya_seen_lucky_drops", Array(I32, 44), when=lt(26)),
            F("gatya_seen_lucky_drops", Ints, when=ge(26)),
            F("show_ban_message", Bool, key="banned"),
            F("catfood_beginner_purchased", Array(Bool, 3)),
            F("next_week_timestamp", F64),
            F("catfood_beginner_expired", Array(Bool, 3)),
            F("rank_up_sale_value", I32),
            Expect(49),
        ),
        Expect(50, when=ge(24)),
        Expect(51, when=ge(25)),
        *group(ge(26), _cats("catguide_collected", gv=False), Expect(52)),
        *group(
            ge(27),
            doubles(
                "time_since_time_check_cumulative",
                "server_timestamp",
                "last_checked_energy_recovery_time",
                "time_since_check",
                "last_checked_expedition_time",
            ),
            F("catfruit", Ints),
            _cats("fourth_forms", gv=False),
            _cats("catseyes_used", gv=False),
            F("catseyes", Ints),
            F("catamins", Ints),
            sec("gamatoto", c.Gamatoto),
            F("unlock_popups_6", Bools),
            sec("ex_stages", c.ExChapters),
            Expect(53),
        ),
        *group(
            ge(29),
            named_part("gamatoto", "helpers"),
            Expect(54),
            sec("item_pack", c.ItemPack),
            Expect(54),
        ),
        *group(
            ge(30),
            named_part("gamatoto", "skin"),
            F("platinum_tickets", I32),
            sec("logins", c.LoginBonus, gv_read=True, gv_init=True),
            F("reset_item_reward_flags", Bools, when=lt(101000)),
            doubles("reward_remaining_time", "last_checked_reward_time"),
            F("announcements", Array(Tuple(I32, I32), 16)),
            ints("backup_counter", "ui12", "ui13", "ui14"),
            Expect(55),
        ),
        *group(
            ge(31),
            F("ub3", Bool),
            part("item_reward_stages", "item_obtains"),
            part("gatya", "stepup"),
            F("backup_frame", I32),
            Expect(56),
        ),
        *group(ge(32), F("ub4", Bool), _cats("favorites", gv=False), Expect(57)),
        *group(
            ge(33),
            Sec(
                "dojo",
                c.Dojo,
                lambda d, s: c.Dojo.read_chapters(d),
                lambda o, d, s: o.write_chapters(d),
                lambda s: c.Dojo.init(),
            ),
            part("dojo", "item_locks"),
            Expect(58),
        ),
        *group(
            ge(34),
            F("last_checked_zombie_time", F64),
            Sec(
                "outbreaks",
                c.Outbreaks,
                lambda d, s: c.Outbreaks.read_chapters(d),
                lambda o, d, s: o.write_chapters(d),
                lambda s: c.Outbreaks.init(),
            ),
            part("outbreaks", "2"),
            sec("scheme_items", c.SchemeItems),
        ),
        *group(
            ge(35),
            part("outbreaks", "current_outbreaks", gv=True),
            F("first_locks", Map(I32, Bool)),
            F("energy_penalty_timestamp", F64),
            Expect(60),
        ),
        *group(
            ge(36),
            _cats("chara_new_flags", gv=False),
            F("shown_maxcollab_mg", Bool),
            named_part("item_pack", "displayed_packs"),
            Expect(61),
        ),
        *group(ge(38), sec("unlock_popups", c.UnlockPopups), Expect(63)),
        *group(
            ge(39),
            sec("ototo", c.Ototo, gv_init=True),
            part("ototo", "2", gv=True),
            F("last_checked_castle_time", F64),
            Expect(64),
        ),
        *group(ge(40), sec("beacon_base", c.BeaconEventListScene), Expect(65)),
        *group(
            ge(41),
            sec("tower", c.TowerChapters),
            sec("missions", c.Missions, gv_read=True),
            named_part("tower", "item_obtain_states"),
            Expect(66),
        ),
        *group(
            ge(42),
            part("dojo", "ranking", gv=True),
            named_part("item_pack", "three_days"),
            sec("challenge", c.ChallengeChapters),
            named_part("challenge", "scores"),
            named_part("challenge", "popup"),
            Expect(67),
        ),
        *group(
            ge(43),
            part("missions", "weekly_missions"),
            Part(
                "dojo",
                lambda o, d, s: o.ranking.read_did_win_rewards(d),
                lambda o, d, s: o.ranking.write_did_win_rewards(d),
            ),
            F("event_update_flags", Bool),
            Expect(68),
        ),
        *group(
            ge(44),
            part("event_stages", "dicts"),
            F("cotc_1_complete", I32),
            Expect(69),
        ),
        *group(ge(46), named_part("gamatoto", "collab"), Expect(71)),
        *group(lt(90300), sec("map_resets", c.MapResets), Expect(72)),
        *group(ge(51), sec("uncanny", c.UncannyChapters), Expect(76)),
        *group(
            ge(77),
            sec("catamin_stages", c.UncannyChapters),
            F("lucky_tickets", Ints),
            F("ub5", Bool),
            Expect(77),
        ),
        *group(
            ge(80000),
            named_part("officer_pass", "gold_pass", gv=True),
            _cats("talents", gv=False),
            F("np", I32),
            F("ub6", Bool),
            Expect(80000),
        ),
        *group(
            ge(80200),
            F("ub7", Bool),
            F("leadership", I16),
            named_part("officer_pass", "cat_data"),
            Expect(80200),
        ),
        *group(
            ge(80300),
            F("filibuster_stage_id", I8),
            F("filibuster_stage_enabled", Bool),
            Expect(80300),
        ),
        *group(ge(80500), F("stage_ids_10s", Ints), Expect(80500)),
        *group(
            ge(80600),
            F("uil6", Array(I32, I16)),
            sec("legend_quest", c.LegendQuestChapters),
            F("ush1", I16),
            F("uby1", I8),
            Expect(80600),
        ),
        *group(ge(80700), F("uiid1", Map(I32, Ints)), Expect(80700)),
        *group(both(ge(100600), lambda s: s.is_en()), F("uby2", I8), Expect(100600)),
        *group(ge(81000), F("restart_pack", I8), Expect(81000)),
        *group(
            ge(90000),
            sec("medals", c.Medals),
            sec("wildcat_slots", c.GamblingEvent, gv_read=True),
            Expect(90000),
        ),
        *group(
            ge(90100),
            shorts("ush2", "ush3"),
            F("ui15", I32),
            F("ud1", F64),
            Expect(90100),
        ),
        *group(
            ge(90300),
            F(
                "utl1",
                Array(PaddedTuple(I32, I32, I16, I32, I32, I32, I16), I16),
            ),
            F("uidd1", Map(I32, F64, I16)),
            sec("gauntlets", c.GauntletChapters),
            Expect(90300),
        ),
        *group(
            ge(90400),
            sec("enigma_clears", c.GauntletChapters),
            sec("enigma", c.Enigma, gv_read=True),
            sec("cleared_slots", c.ClearedSlots),
            Expect(90400),
        ),
        *group(
            ge(90500),
            sec("collab_gauntlets", c.GauntletChapters),
            F("ub8", Bool),
            doubles("ud2", "ud3"),
            F("ui16", I32),
            group(
                ge(100300),
                F("uby3", I8),
                F("ub9", Bool),
                doubles("ud4", "ud5"),
            ),
            group(
                ge(130700),
                F("uiid3", Map(I32, I8, I16)),
                F("uidd2", Map(I32, F64, I16)),
            ),
            F("uidd3", Map(I32, F64, I16), when=ge(140100)),
            Expect(90500),
        ),
        *group(
            ge(90700),
            sec("talent_orbs", c.TalentOrbs, gv_read=True),
            F("uidiid2", Map(I16, Map(I8, I16, I8), I16)),
            F("ub10", Bool),
            Expect(90700),
        ),
        *group(
            ge(90800),
            F("uil7", Array(I32, I16)),
            F("ubl2", Array(Bool, 10)),
            Expect(90800),
        ),
        *group(
            ge(90900),
            sec("cat_shrine", c.CatShrine),
            doubles("ud6", "ud7"),
            Expect(90900),
        ),
        *group(ge(91000), part("lineups", "slot_names", gv=True), Expect(91000)),
        *group(
            ge(100000),
            F("legend_tickets", I32),
            F("uiil1", Array(Tuple(I8, I32), I8)),
            bools("ub11", "ub12"),
            F("password_refresh_token", String),
            F("ub13", Bool),
            bytes_("uby4", "uby5"),
            doubles("ud8", "ud9"),
            Expect(100000),
        ),
        *group(ge(100100), F("date_int", I32), Expect(100100)),
        *group(ge(100300), part("battle_items", "endless_items"), Expect(100300)),
        *group(
            ge(100400),
            F("event_capsules_2", Array(I32, I8)),
            F("two_battle_lines", Bool),
            Expect(100400),
        ),
        *group(
            ge(100600),
            F("ud10", F64),
            F("platinum_shards", I32),
            F("ub15", Bool),
            Expect(100600),
        ),
        *group(
            ge(100700),
            sec("cat_scratcher", c.GamblingEvent, gv_read=True),
            Expect(100700),
        ),
        *group(
            ge(100900),
            sec("aku", c.AkuChapters),
            bools("ub16", "ub17"),
            F("ushdshd2", Map(I16, Shorts, I16)),
            F("ushdd", Map(I16, F64, I16)),
            F("ushdd2", Map(I16, F64, I16)),
            F("ub18", Bool),
            Expect(100900),
        ),
        *group(ge(101000), F("uby6", I8), Expect(101000)),
        *group(ge(110000), F("uidtii", Map(I32, Tuple(I8, I8), I16)), Expect(110000)),
        *group(
            ge(110500),
            sec("behemoth_culling", c.GauntletChapters),
            F("ub19", Bool),
            Expect(110500),
        ),
        *group(ge(110600), F("ub20", Bool), Expect(110600)),
        *group(
            ge(110700),
            F("uidtff", Map(I32, Tuple(F64, F64))),
            F("ub20", Bool, when=not_jp),
            Expect(110700),
        ),
        *group(
            ge(110800),
            named_part("cat_shrine", "dialogs"),
            bools("ub21", "dojo_3x_speed", "ub22", "ub23"),
            Expect(110800),
        ),
        *group(
            ge(111000),
            F("ui17", I32),
            F("ush4", I16),
            bytes_("uby7", "uby8"),
            F("ub24", Bool),
            F("uby9", I8),
            F("ushl1", Array(I16, I8)),
            F("ushl2", Shorts),
            F("ushl3", Shorts),
            ints("ui18", "ui19", "ui20"),
            shorts("ush5", "ush6", "ush7", "ush8"),
            F("uby10", I8),
            bools("ub25", "ub26", "ub27", "ub28", "ub29", "ub30"),
            F("uby11", I8),
            F("ushl4", Shorts),
            F("ubl3", Array(Bool, 14)),
            F("labyrinth_medals", Array(I16, I8)),
            Expect(111000),
        ),
        *group(
            ge(120000),
            sec("zero_legends", c.ZeroLegendsChapters),
            F("uby12", I8),
            Expect(120000),
        ),
        *group(ge(120100), F("ushl6", Shorts), Expect(120100)),
        *group(
            ge(120200),
            F("ub31", Bool),
            F("ush9", I16),
            F("ushshd", Map(I16, I16, I8)),
            Expect(120200),
        ),
        *group(ge(120400), doubles("ud11", "ud12"), Expect(120400)),
        *group(
            ge(120500),
            bools("ub32", "ub33", "ub34"),
            F("ui21", I32),
            F("golden_cpu_count", I8),
            Expect(120500),
        ),
        *group(
            ge(120600),
            bytes_("sound_effects_volume", "background_music_volume"),
            Expect(120600),
        ),
        *group(
            lambda s: (
                (s.not_jp() and s.game_version >= 120700)
                or (s.is_jp() and s.game_version >= 130000)
            ),
            F("ustl1", Array(Tuple(String, String), I8)),
            Expect(120700, when=not_jp),
            Expect(130000, when=jp),
        ),
        *group(ge(130100), F("utl3", Array(Tuple(I32, I64))), Expect(130100)),
        *group(ge(130301), F("ustid1", Map(String, Tuple(I32, F64))), Expect(130301)),
        *group(ge(130400), doubles("ud13", "ud14"), Expect(130400)),
        *group(
            ge(130500),
            F(
                "utl4",
                Array(Tuple(I8, Array(Tuple(I8, I8, I8, Shorts), I8)), I16),
            ),
            Expect(130500),
        ),
        *group(
            ge(130600),
            F("uby14", I8),
            F("ush12", I16, when=not_jp),
            Expect(130600),
        ),
        *group(
            ge(130700),
            F("ush12", I16, when=jp),
            F("ud15", F64),
            bytes_("uby15", "uby16"),
            F("ush11", I16),
            bytes_("uby17", "uby18", "uby19"),
            F("ud16", F64),
            F("ushd1", Map(I16, Tuple(I16, I32, Map(I16, I16, I16)), I16)),
            Expect(130700),
        ),
        *group(
            ge(140000),
            F("ui22", I32),
            F("ud17", F64),
            F("uby20", I8),
            F("uild1", Map(I32, Array(I8, I8), I8)),
            sec("dojo_chapters", c.ZeroLegendsChapters),
            F("uil9", Array(I32, I16)),
            F("ub35", Bool),
            F("ud18", F64),
            F("ushd2", Map(I16, I8, I16)),
            Expect(140000),
        ),
        *group(
            lambda s: 140100 <= s.game_version < 140500,
            F("uby21", I8),
            Expect(140100),
        ),
        *group(
            ge(140200),
            F("uil10", Array(Uil10Codec(), I8)),
            F("uid1", Map(I32, F64, I8)),
            F("hundred_million_ticket", I32),
            Expect(140200),
        ),
        *group(
            ge(140300),
            F("uil11", Array(I8, I8)),
            group(ge(150300), F("ui24", I32), F("ub38", Bool)),
            F("ub39", Bool, when=ge(150500)),
            F("ub36", Bool),
            F("treasure_chests", Array(I32, I8)),
            F("ui23", I32),
            F("uil13", Array(I32, I16)),
            F("ub37", Bool),
            Expect(140300),
        ),
        F("remaining_data", Rest),
    ]
    return L


def _flatten(entries: Iterable[Entry | list[Entry]]) -> list[Entry]:
    out: list[Entry] = []
    for e in entries:
        out.extend(_flatten(e) if isinstance(e, list) else [e])
    return out


@functools.cache
def layout() -> list[Entry]:
    """Every entry in storage order (built on first use, once the section
    classes have been imported)."""
    return _flatten(_build())


# --- driving the layout ---------------------------------------------------


def run_read(s: SaveFile, data: Data) -> None:
    gv = s.game_version
    for e in layout():
        if not e.when(s):
            continue
        match e:
            case F(binary=True):
                setattr(s, e.name, e.codec.read(data, gv))
            case Sec():
                setattr(s, e.name, e.read(data, s))
            case Part():
                e.read(getattr(s, e.name), data, s)
            case Expect():
                data.expect_int(e.value)
            case Dst():
                s.read_dst()
            case Raw():
                e.read(data, s)
            case _:
                pass


def run_write(s: SaveFile, data: Data) -> None:
    gv = s.game_version
    for e in layout():
        if not e.when(s):
            continue
        match e:
            case F(binary=True):
                e.codec.write(data, getattr(s, e.name), gv)
            case Sec():
                e.write(getattr(s, e.name), data, s)
            case Part():
                e.write(getattr(s, e.name), data, s)
            case Expect():
                data.write_int(e.value)
            case Dst():
                s.write_dst()
            case Raw():
                e.write(data, s)
            case _:
                pass


@functools.cache
def fields() -> list[F | Sec]:
    """Each JSON field once (its first entry), in layout order."""
    seen: set[str] = set()
    out: list[F | Sec] = []
    for e in layout():
        if isinstance(e, (F, Sec)) and e.name not in seen:
            seen.add(e.name)
            out.append(e)
    return out


def to_json(s: SaveFile) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for e in fields():
        value = getattr(s, e.name)
        out[e.json_key] = (
            value.serialize() if isinstance(e, Sec) else e.codec.to_json(value)
        )
    return out


def from_json(s: SaveFile, data: dict[str, Any]) -> None:
    """Set every field found in `data`; the rest keep their current values."""
    for e in fields():
        if e.json_key not in data:
            continue
        value = data[e.json_key]
        if isinstance(e, Sec):
            setattr(s, e.name, e.cls.deserialize(value))
        else:
            setattr(s, e.name, e.codec.from_json(value))


def init_values(s: SaveFile) -> None:
    """Give every field its value for a new save of `s`'s version and region.

    Where a field is declared more than once, the entry stored for this
    version decides its default (e.g. a fixed-length list's length); if
    none is, the last (newest) one does.
    """
    chosen: dict[str, F | Sec] = {}
    for e in layout():
        if not isinstance(e, (F, Sec)):
            continue
        current = chosen.get(e.name)
        if current is None or not current.when(s):
            chosen[e.name] = e
    for name, e in chosen.items():
        setattr(s, name, e.init(s) if isinstance(e, Sec) else e.codec.default())
