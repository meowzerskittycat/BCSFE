from __future__ import annotations
from dataclasses import dataclass
from typing import Any, ClassVar

from bcsfe.core.io.schema import I32, Array, Map, Nested, Struct, field


@dataclass
class Login(Struct):
    __transparent__: ClassVar[bool] = True
    count: int = field(I32)


@dataclass
class Logins(Struct):
    __transparent__: ClassVar[bool] = True
    logins: list[Login] = field(Array(Nested(Login)))


@dataclass
class LoginSets(Struct):
    __transparent__: ClassVar[bool] = True
    logins: list[Logins] = field(Array(Nested(Logins)))


@dataclass
class LoginBonus(Struct):
    """Login bonus progress. Before 8.0 it was a list of sets; since then a
    map from bonus id."""

    old_logins: LoginSets = field(Nested(LoginSets), before=80000)
    logins: dict[int, Login] = field(Map(I32, Nested(Login)), since=80000)

    @classmethod
    def init(cls, gv: Any = None) -> LoginBonus:
        return cls()

    def get_login(self, id: int) -> Login | None:
        return self.logins.get(id)
