from dataclasses import dataclass

from bcsfe.core.game.map.chapters import Chapters
from bcsfe.core.io.schema import I32, Array, Bool, Section, Struct, field


@dataclass
class ChallengeChapters(Struct):
    chapters: Chapters = field(Section(Chapters))
    scores: list[int] = field(Array(I32), part="scores")
    shown_popup: bool = field(Bool, part="popup")
