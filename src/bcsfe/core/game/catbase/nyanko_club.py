import datetime
import random
import time
from dataclasses import dataclass

from bcsfe import core
from bcsfe.cli import dialog_creator, color
from bcsfe.core.io.schema import F64, I32, Bool, Map, Struct, field


@dataclass
class NyankoClub(Struct):
    """Gold pass (officer club) membership."""

    officer_id: int = field(I32)
    total_renewal_times: int = field(I32)
    start_date_now: float = field(F64)
    end_date_now: float = field(F64)
    start_date_next: float = field(F64)
    end_date_next: float = field(F64)
    start_date_total: float = field(F64)
    end_date_total: float = field(F64)
    time_error_end: float = field(F64)
    total_state_updates: int = field(I32)
    login_bonus_date: float = field(F64)
    claimed_rewards: dict[int, int] = field(Map(I32, I32))
    remaing_days_popup: float = field(F64)
    first_popup_flag: bool = field(Bool)
    badge_flag: bool = field(Bool, since=80100)

    def get_gold_pass(self, officer_id: int, total_days: int, save_file: core.SaveFile):
        self.officer_id = officer_id
        start_date_now = int(time.time())
        end_date_now = (
            start_date_now + datetime.timedelta(days=total_days).total_seconds()
        )
        end_date_total = (
            start_date_now + datetime.timedelta(days=total_days * 2).total_seconds()
        )

        self.total_renewal_times = 2
        self.start_date_now = start_date_now
        self.end_date_now = end_date_now

        self.start_date_next = end_date_now
        self.end_date_next = end_date_total

        self.start_date_total = start_date_now
        self.end_date_total = end_date_total

        self.time_error_end = start_date_now

        self.total_state_updates = 2

        self.login_bonus_date = end_date_now

        self.remaing_days_popup = 0.0
        self.first_popup_flag = True
        self.badge_flag = False

        login = save_file.logins.get_login(5100)
        if login is not None:
            login.count = 0

        self.claimed_rewards = {}

    def remove_gold_pass(self, save_file: core.SaveFile):
        self.officer_id = -1
        self.total_renewal_times = 0
        self.start_date_now = 0.0
        self.end_date_now = 0.0
        self.start_date_next = 0.0
        self.end_date_next = 0.0
        self.start_date_total = 0.0
        self.end_date_total = 0.0
        self.time_error_end = 0.0
        self.total_state_updates = 0
        self.login_bonus_date = 0.0
        self.remaing_days_popup = 0.0
        self.first_popup_flag = False
        self.badge_flag = False

        login = save_file.logins.get_login(5100)
        if login is not None:
            login.count = 0

        self.claimed_rewards = {}

    @staticmethod
    def get_random_officer_id() -> int:
        return random.randint(1, 2**16 - 1)

    @staticmethod
    def edit_gold_pass(save_file: core.SaveFile):
        club = save_file.officer_pass.gold_pass

        officer_id = color.color_input_key("gold_pass_dialog").strip()
        if not officer_id:
            officer_id = NyankoClub.get_random_officer_id()

        if officer_id == "-1":
            officer_id = -1
        else:
            try:
                officer_id = int(officer_id)
            except ValueError:
                officer_id = NyankoClub.get_random_officer_id()
            officer_id = dialog_creator.MaxValue.i32().clamp(officer_id)

        if officer_id == -1:
            club.remove_gold_pass(save_file)
            color.color_print_key("gold_pass_remove_success")
        else:
            club.get_gold_pass(officer_id, 30, save_file)
            color.color_print_key("gold_pass_get_success", id=officer_id)
