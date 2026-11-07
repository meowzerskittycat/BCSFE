import datetime
from typing import Any

from bcsfe import __version__, core
from bcsfe.core import messages
from bcsfe.core.io import save_layout
from bcsfe.core.io.save_layout import from_timestamp, to_timestamp

__all__ = ["SaveFile", "from_timestamp", "to_timestamp"]

from bcsfe.core.io.config import ConfigKey


class SaveError(Exception):
    pass


class CantDetectSaveCCError(SaveError):
    pass


class FailedToLoadError(SaveError):
    pass


class FailedToSaveError(SaveError):
    pass


class SaveFile:
    # The save's fields, in storage order. They're read, written and turned
    # into JSON by `save_layout`; these declarations only give them types
    # (tests/test_roundtrip.py checks they match the layout).
    dsts: list[bool]
    ub1: bool
    mute_bgm: bool
    mute_se: bool
    catfood: int
    current_energy: int
    year: int
    month: int
    day: int
    timestamp: float
    date: datetime.datetime
    ui1: int
    stamp_value_save: int
    ui2: int
    upgrade_state: int
    xp: int
    tutorial_state: int
    ui3: int
    koreaSuperiorTreasureState: int
    unlock_popups_11: list[int]
    ui5: int
    unlock_enemy_guide: int
    ui6: int
    ub0: bool
    ui7: int
    cleared_eoc_1: int
    ui8: int
    unlocked_ending: int
    lineups: core.LineUps
    stamp_data: core.StampData
    story: core.StoryChapters
    enemy_guide: list[int]
    cats: core.Cats
    special_skills: core.SpecialSkills
    menu_unlocks: list[int]
    unlock_popups_0: list[int]
    battle_items: core.BattleItems
    new_dialogs_2: list[int]
    uil1: list[int]
    moneko_bonus: list[int]
    daily_reward_initialized: list[int]
    date_2: datetime.datetime
    date_3: datetime.datetime
    ui0: int
    stage_unlock_cat_value: int
    show_ending_value: int
    chapter_clear_cat_unlock: int
    ui9: int
    ios_android_month: int
    ui10: int
    save_data_4_hash: str
    mysale: core.MySale
    chara_flags: list[int]
    uim1: int
    ubm1: bool
    chara_flags_2: list[int]
    normal_tickets: int
    rare_tickets: int
    event_stages: core.EventChapters
    itf1_ending: int
    continue_flag: int
    unlock_popups_8: list[int]
    unit_drops: list[int]
    gatya: core.Gatya
    get_event_data: bool
    achievements: list[bool]
    os_value: int
    date_4: datetime.datetime
    player_id: str
    order_ids: list[str]
    g_timestamp: float
    g_servertimestamp: float
    m_gettimesave: float
    usl1: list[str]
    energy_notification: bool
    full_gameversion: int
    uil2: list[int]
    uil3: list[int]
    uil4: list[int]
    g_timestamp_2: float
    g_servertimestamp_2: float
    m_gettimesave_2: float
    unknown_timestamp: float
    usl2: list[str]
    m_dGetTimeSave2: float
    ui11: int
    ubl1: list[bool]
    user_rank_rewards: core.UserRankRewards
    transfer_code: str
    confirmation_code: str
    transfer_flag: bool
    item_reward_stages: core.ItemRewardChapters
    timed_score_stages: core.TimedScoreChapters
    inquiry_code: str
    officer_pass: core.OfficerPass
    has_account: int
    backup_state: int
    ub2: bool
    itf1_complete: int
    title_chapter_bg: int
    combo_unlocks: list[int]
    combo_unlocked_10k_ur: bool
    event_capsules: list[int]
    event_capsules_counter: list[int]
    m_dGetTimeSave3: float
    gatya_seen_lucky_drops: list[int]
    show_ban_message: bool
    catfood_beginner_purchased: list[bool]
    next_week_timestamp: float
    catfood_beginner_expired: list[bool]
    rank_up_sale_value: int
    time_since_time_check_cumulative: float
    server_timestamp: float
    last_checked_energy_recovery_time: float
    time_since_check: float
    last_checked_expedition_time: float
    catfruit: list[int]
    catseyes: list[int]
    catamins: list[int]
    gamatoto: core.Gamatoto
    unlock_popups_6: list[bool]
    ex_stages: core.ExChapters
    item_pack: core.ItemPack
    platinum_tickets: int
    logins: core.LoginBonus
    reset_item_reward_flags: list[bool]
    reward_remaining_time: float
    last_checked_reward_time: float
    announcements: list[tuple[int, int]]
    backup_counter: int
    ui12: int
    ui13: int
    ui14: int
    ub3: bool
    backup_frame: int
    ub4: bool
    dojo: core.Dojo
    last_checked_zombie_time: float
    outbreaks: core.Outbreaks
    scheme_items: core.SchemeItems
    first_locks: dict[int, bool]
    energy_penalty_timestamp: float
    shown_maxcollab_mg: bool
    unlock_popups: core.UnlockPopups
    ototo: core.Ototo
    last_checked_castle_time: float
    beacon_base: core.BeaconEventListScene
    tower: core.TowerChapters
    missions: core.Missions
    challenge: core.ChallengeChapters
    event_update_flags: bool
    cotc_1_complete: int
    map_resets: core.MapResets
    uncanny: core.UncannyChapters
    catamin_stages: core.UncannyChapters
    lucky_tickets: list[int]
    ub5: bool
    np: int
    ub6: bool
    ub7: bool
    leadership: int
    filibuster_stage_id: int
    filibuster_stage_enabled: bool
    stage_ids_10s: list[int]
    uil6: list[int]
    legend_quest: core.LegendQuestChapters
    ush1: int
    uby1: int
    uiid1: dict[int, list[int]]
    uby2: int
    restart_pack: int
    medals: core.Medals
    wildcat_slots: core.GamblingEvent
    ush2: int
    ush3: int
    ui15: int
    ud1: float
    utl1: list[tuple[int, int, int, int, int, int, int]]
    uidd1: dict[int, float]
    gauntlets: core.GauntletChapters
    enigma_clears: core.GauntletChapters
    enigma: core.Enigma
    cleared_slots: core.ClearedSlots
    collab_gauntlets: core.GauntletChapters
    ub8: bool
    ud2: float
    ud3: float
    ui16: int
    uby3: int
    ub9: bool
    ud4: float
    ud5: float
    uiid3: dict[int, int]
    uidd2: dict[int, float]
    uidd3: dict[int, float]
    talent_orbs: core.TalentOrbs
    uidiid2: dict[int, dict[int, int]]
    ub10: bool
    uil7: list[int]
    ubl2: list[bool]
    cat_shrine: core.CatShrine
    ud6: float
    ud7: float
    legend_tickets: int
    uiil1: list[tuple[int, int]]
    ub11: bool
    ub12: bool
    password_refresh_token: str
    ub13: bool
    uby4: int
    uby5: int
    ud8: float
    ud9: float
    date_int: int
    event_capsules_2: list[int]
    two_battle_lines: bool
    ud10: float
    platinum_shards: int
    ub15: bool
    cat_scratcher: core.GamblingEvent
    aku: core.AkuChapters
    ub16: bool
    ub17: bool
    ushdshd2: dict[int, list[int]]
    ushdd: dict[int, float]
    ushdd2: dict[int, float]
    ub18: bool
    uby6: int
    uidtii: dict[int, tuple[int, int]]
    behemoth_culling: core.GauntletChapters
    ub19: bool
    ub20: bool
    uidtff: dict[int, tuple[float, float]]
    ub21: bool
    dojo_3x_speed: bool
    ub22: bool
    ub23: bool
    ui17: int
    ush4: int
    uby7: int
    uby8: int
    ub24: bool
    uby9: int
    ushl1: list[int]
    ushl2: list[int]
    ushl3: list[int]
    ui18: int
    ui19: int
    ui20: int
    ush5: int
    ush6: int
    ush7: int
    ush8: int
    uby10: int
    ub25: bool
    ub26: bool
    ub27: bool
    ub28: bool
    ub29: bool
    ub30: bool
    uby11: int
    ushl4: list[int]
    ubl3: list[bool]
    labyrinth_medals: list[int]
    zero_legends: core.ZeroLegendsChapters
    uby12: int
    ushl6: list[int]
    ub31: bool
    ush9: int
    ushshd: dict[int, int]
    ud11: float
    ud12: float
    ub32: bool
    ub33: bool
    ub34: bool
    ui21: int
    golden_cpu_count: int
    sound_effects_volume: int
    background_music_volume: int
    ustl1: list[tuple[str, str]]
    utl3: list[tuple[int, int]]
    ustid1: dict[str, tuple[int, float]]
    ud13: float
    ud14: float
    utl4: list[tuple[int, list[tuple[int, int, int, list[int]]]]]
    uby14: int
    ush12: int
    ud15: float
    uby15: int
    uby16: int
    ush11: int
    uby17: int
    uby18: int
    uby19: int
    ud16: float
    ushd1: dict[int, tuple[int, int, dict[int, int]]]
    ui22: int
    ud17: float
    uby20: int
    uild1: dict[int, list[int]]
    dojo_chapters: core.ZeroLegendsChapters
    uil9: list[int]
    ub35: bool
    ud18: float
    ushd2: dict[int, int]
    uby21: int
    uil10: list[tuple[Any, ...]]
    uid1: dict[int, float]
    hundred_million_ticket: int
    uil11: list[int]
    ui24: int
    ub38: bool
    ub39: bool
    ub36: bool
    treasure_chests: list[int]
    ui23: int
    uil13: list[int]
    ub37: bool
    remaining_data: bytes

    def __init__(
        self,
        dt: core.Data | None = None,
        cc: core.CountryCode | None = None,
        load: bool = True,
        gv: core.GameVersion | None = None,
        package_name: str | None = None,
    ):
        self.package_name = package_name
        self.save_path: core.Path | None = None
        if dt is None:
            self.data = core.Data()
        else:
            self.data = dt
        detected_cc = self.detect_cc()
        if detected_cc is None:
            if cc is None:
                raise CantDetectSaveCCError(
                    core.core_data.local_manager.get_key("cant_detect_cc")
                )
            self.cc = cc
        else:
            self.cc = detected_cc

        self.localizable: core.Localizable | None = None

        self.init_save(gv)

        if dt is not None and load:
            self.load_wrapper()

    def get_localizable(self) -> core.Localizable:
        if self.localizable is None:
            self.localizable = core.Localizable(self)
        return self.localizable

    def load_save_file(self, other: SaveFile):
        self.data = other.data
        self.cc = other.cc
        self.game_version = other.game_version
        self.init_save(other.game_version)
        self.load_wrapper()

    def detect_cc(self) -> core.CountryCode | None:
        for cc in core.CountryCode.get_all():
            self.cc = cc
            if self.verify_hash():
                return cc
        return None

    def get_salt(self) -> str:
        """Get the salt for the save file. This is used for hashing the save file.

        Returns:
            str: The salt
        """
        salt = f"battlecats{self.cc.get_patching_code()}"
        return salt

    def get_current_hash(self) -> str | None:
        """Get the current hash for the save file. This is used for hashing the save file.

        Returns:
            str: The current hash
        """
        self.data.reset_pos()
        self.data.set_pos(-32)
        try:
            hash = self.data.read_string(32)
        except UnicodeDecodeError, core.EndOfDataError:
            return None
        return hash

    def get_new_hash(self, existing_hash: bool = True) -> str:
        """Get the new hash for the save file. This is used for hashing the save file.

        Returns:
            str: The new hash
        """
        salt = self.get_salt()
        self.data.reset_pos()
        if existing_hash:
            data_to_hash = self.data.read_bytes(len(self.data) - 32)
        else:
            data_to_hash = self.data.read_bytes(len(self.data))
        salted_data = core.Data(salt.encode("utf-8") + data_to_hash)
        hash = core.Hash(core.HashAlgorithm.MD5).get_hash(salted_data)
        return hash.to_hex()

    def set_hash(self, add: bool = False):
        """Set the hash of the save file."""
        hash = self.get_new_hash(existing_hash=not add)
        if not add:
            self.data.set_pos(-32)
        else:
            self.data.set_pos(len(self.data))
        self.data.write_string(hash, write_length=False)

    def verify_hash(self) -> bool:
        """Verify the hash of the save file.

        Returns:
            bool: Whether the hash is valid
        """
        current_hash = self.get_current_hash()
        if current_hash is None:
            return False
        return current_hash == self.get_new_hash()

    def load_wrapper(self):
        try:
            self.load()
        except Exception as e:
            ignore_error = core.core_data.config.get_bool(ConfigKey.IGNORE_PARSE_ERROR)
            if not ignore_error:
                raise FailedToLoadError(
                    core.core_data.local_manager.get_key("failed_to_load_save")
                ) from e
            else:
                from traceback import format_exc

                messages.show("parse_ignored_error", error=format_exc())

    def set_gv(self, gv: core.GameVersion):
        self.game_version = gv

    def set_cc(self, cc: core.CountryCode):
        self.cc = cc
        self.set_package_name(None)

    def set_package_name(self, package_name: str | None):
        self.package_name = package_name

    def load(self):
        """Read every field from `self.data` (see `save_layout`)."""
        self.data.reset_pos()
        self.dst_index = 0
        self.dsts = []
        self.game_version = core.GameVersion(self.data.read_int())
        save_layout.run_read(self, self.data)

    def save(self, data: core.Data):
        """Write every field to `data`, without the hash."""
        self.data = data
        self.dst_index = 0
        self.data.clear()
        self.data.enable_buffer()
        self.data.write_int(self.game_version.game_version)
        save_layout.run_write(self, self.data)
        self.data.end_buffer()

    def to_data(self) -> core.Data:
        dt = core.Data()
        self.save_wrapper(dt)
        self.set_hash(add=True)
        return dt

    def save_wrapper(self, data: core.Data) -> None:
        try:
            self.save(data)
        except Exception as e:
            raise FailedToSaveError(
                core.core_data.local_manager.get_key("failed_to_save_save")
            ) from e

    def to_file(self, path: core.Path) -> None:
        path.parent().generate_dirs()
        dt = self.to_data()
        try:
            dt.to_file(path)
        except Exception as e:
            print(e)

    @staticmethod
    def get_temp_path() -> core.Path:
        save_temp_path = core.Path.get_data_folder().add("save.temp")
        save_temp_path.parent().generate_dirs()
        return save_temp_path

    def to_dict(self) -> dict[str, Any]:
        return {
            "editor_version": __version__,
            "cc": self.cc.get_code(),
            "game_version": self.game_version.game_version,
            **save_layout.to_json(self),
        }

    @staticmethod
    def from_dict(data: dict[str, Any], warn: bool = True) -> SaveFile:
        """A save from `to_dict` output. Missing fields get new-save values."""
        editor_version = data.get("editor_version", "0.0.0")
        if editor_version != __version__ and warn:
            messages.show(
                "editor_version_mismatch",
                json_version=editor_version,
                editor_version=__version__,
            )
        cc = data.get("cc")
        save_file = SaveFile(
            cc=core.CountryCode(cc) if cc is not None else None,
            gv=core.GameVersion(data.get("game_version", 0)),
        )
        save_layout.from_json(save_file, data)
        return save_file

    def init_save(self, gv: core.GameVersion | None = None):
        """Reset every field to its value in a new save of version `gv`."""
        self.dsts = []
        self.dst_index = 0
        self.set_gv(gv if gv is not None else core.GameVersion(120200))
        save_layout.init_values(self)

    def is_jp(self) -> bool:
        return self.cc == core.CountryCodeType.JP

    def not_jp(self) -> bool:
        return self.cc != core.CountryCodeType.JP

    def is_en(self) -> bool:
        return self.cc == core.CountryCodeType.EN

    def should_read_dst(self) -> bool:
        if self.is_jp():
            return False
        return self.game_version >= 49

    def read_dst(self):
        if self.should_read_dst():
            self.dsts.append(self.data.read_bool())

    def write_dst(self):
        if self.should_read_dst():
            try:
                self.data.write_bool(self.dsts[self.dst_index])
            except IndexError:
                self.data.write_bool(False)
            self.dst_index += 1

    def calculate_user_rank(self):
        user_rank = 0
        for cat in self.cats.cats:
            if not cat.unlocked:
                continue
            user_rank += cat.upgrade.base + 1
            user_rank += cat.upgrade.plus

        for i, skill in enumerate(self.special_skills.skills):
            if i == 1:
                continue
            user_rank += skill.upgrade.base + 1
            user_rank += skill.upgrade.plus

        return user_rank

    @staticmethod
    def get_string_identifier(identifier: str) -> str:
        return f"_bcsfe:{identifier}"

    def store_string(self, identifier: str, string: str, overwrite: bool = True):
        if overwrite:
            for i, order in enumerate(self.order_ids):
                if order.startswith(SaveFile.get_string_identifier(identifier)):
                    self.order_ids[i] = (
                        f"{SaveFile.get_string_identifier(identifier)}:{string}"
                    )
                    return
        self.order_ids.append(f"{SaveFile.get_string_identifier(identifier)}:{string}")

    def get_string(self, identifier: str) -> str | None:
        for order in self.order_ids:
            if order.startswith(SaveFile.get_string_identifier(identifier)):
                return order.split(":")[2]
        return None

    def get_strings(self, identifier: str) -> list[str]:
        strings: list[str] = []
        for order in self.order_ids:
            if order.startswith(SaveFile.get_string_identifier(identifier)):
                strings.append(order.split(":")[2])

        return strings

    def remove_string(self, identifier: str):
        for i, order in enumerate(self.order_ids):
            if order.startswith(SaveFile.get_string_identifier(identifier)):
                self.order_ids.pop(i)
                return

    def remove_strings(self, identifier: str):
        new_order_ids: list[str] = []
        for order in self.order_ids:
            if not order.startswith(SaveFile.get_string_identifier(identifier)):
                new_order_ids.append(order)
        self.order_ids = new_order_ids

    def store_dict(
        self,
        identifier: str,
        dictionary: dict[str, str],
        overwrite: bool = True,
    ):
        if overwrite:
            self.remove_strings(identifier)

        for key, value in dictionary.items():
            self.order_ids.append(
                f"{SaveFile.get_string_identifier(identifier)}:{key}:{value}"
            )

    def get_dict(self, identifier: str) -> dict[str, str] | None:
        dictionary: dict[str, str] = {}
        for order in self.order_ids:
            if order.startswith(SaveFile.get_string_identifier(identifier)):
                dictionary[order.split(":")[2]] = order.split(":")[3]

        return dictionary

    def remove_dict(self, identifier: str):
        new_order_ids: list[str] = []
        for order in self.order_ids:
            if not order.startswith(SaveFile.get_string_identifier(identifier)):
                new_order_ids.append(order)
        self.order_ids = new_order_ids

    @staticmethod
    def get_saves_path() -> core.Path:
        return core.Path.get_data_folder().add("saves").generate_dirs()

    @staticmethod
    def get_save_path() -> core.Path:
        return SaveFile.get_saves_path().add("SAVE_DATA")

    def get_default_path(self) -> core.Path:
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        local_path = (
            self.get_saves_path()
            .add("backups")
            .add(f"{self.cc.get_code()}")
            .add(self.inquiry_code)
        )
        local_path.generate_dirs()
        local_path = local_path.add(date)
        core.Thread("check-backups", SaveFile.check_backups, []).start()

        return local_path

    @staticmethod
    def get_backups() -> list[tuple[core.Path, datetime.datetime, str, str]]:
        """Every backup made when a save was loaded, newest first, as (path,
        when, country code, inquiry code)."""
        saves_path = SaveFile.get_saves_path().add("backups")
        if not saves_path.exists():
            return []
        backups: list[tuple[core.Path, datetime.datetime, str, str]] = []
        for cc in saves_path.get_dirs():
            for inquiry in cc.get_dirs():
                for save in inquiry.get_paths_dir():
                    try:
                        date = datetime.datetime.strptime(
                            save.basename(), "%Y-%m-%d_%H-%M-%S"
                        )
                    except ValueError:
                        continue
                    backups.append((save, date, cc.basename(), inquiry.basename()))
        backups.sort(key=lambda backup: backup[1], reverse=True)
        return backups

    @staticmethod
    def check_backups():
        max_backups = core.core_data.config.get_int(core.ConfigKey.MAX_BACKUPS)
        # -1 means keep them all. Treat any negative the same: slicing by a
        # negative number would delete the newest backups instead.
        if max_backups < 0:
            return
        saves_path = SaveFile.get_saves_path().add("backups")
        saves_path.generate_dirs()
        for save, *_ in SaveFile.get_backups()[max_backups:]:
            save.remove()

        for cc in saves_path.get_dirs():
            dirs = cc.get_dirs()
            if len(dirs) == 0:
                cc.remove()
            for inquiry in dirs:
                saves = inquiry.get_paths_dir()
                if len(saves) == 0:
                    inquiry.remove()

    def unlock_equip_menu(self):
        self.menu_unlocks[2] = max(self.menu_unlocks[2], 1)

    def set_catfood(self, catfood: int):
        self.catfood = catfood
