from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.game.map.chapters import Chapters
from bcsfe.core.io.schema import I32, Array, Bool, Section, Struct, field
from bcsfe.cli import dialog_creator


@dataclass
class ChallengeChapters(Struct):
    chapters: Chapters = field(Section(Chapters))
    scores: list[int] = field(Array(I32), part="scores")
    shown_popup: bool = field(Bool, part="popup")

    def edit_score(self):
        if not self.scores:
            self.scores = [0]
        self.scores[0] = dialog_creator.edit_int_key(
            "challenge_score",
            self.scores[0],
            dialog_creator.MaxValue.i32().hide_max(),
        )
        self.shown_popup = True
        self.chapters.clear_stage(0, 0, 0, False)


def edit_challenge_score(save_file: core.SaveFile):
    save_file.challenge.edit_score()
