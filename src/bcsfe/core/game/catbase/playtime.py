from dataclasses import dataclass


@dataclass
class PlayTime:
    frames: int

    @staticmethod
    def get_fps() -> int:
        return 30

    @property
    def seconds(self) -> int:
        return self.frames // self.get_fps()

    @property
    def minutes(self) -> int:
        return self.seconds // 60

    @property
    def hours(self) -> int:
        return self.minutes // 60

    @property
    def just_seconds(self) -> int:
        return self.seconds % 60

    @property
    def just_minutes(self) -> int:
        return self.minutes % 60

    @property
    def just_hours(self) -> int:
        return self.hours % 60

    @staticmethod
    def from_hours(hours: int) -> PlayTime:
        return PlayTime(hours * 60 * 60 * PlayTime.get_fps())

    @staticmethod
    def from_minutes(minutes: int) -> PlayTime:
        return PlayTime(minutes * 60 * PlayTime.get_fps())

    @staticmethod
    def from_seconds(seconds: int) -> PlayTime:
        return PlayTime(seconds * PlayTime.get_fps())

    @staticmethod
    def from_hours_mins_secs(hours: int, minutes: int, seconds: int) -> PlayTime:
        return (
            PlayTime.from_hours(hours)
            + PlayTime.from_minutes(minutes)
            + PlayTime.from_seconds(seconds)
        )

    def __add__(self, other: PlayTime) -> PlayTime:
        return PlayTime(self.frames + other.frames)
