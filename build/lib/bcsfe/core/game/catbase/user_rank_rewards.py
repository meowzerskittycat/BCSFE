from bcsfe import core


class RankGift:
    def __init__(self, index: int, threshold: int, rewards: list[tuple[int, int]]):
        self.index = index
        self.threshold = threshold
        self.rewards = rewards

    def get_name(self, rank_gift_descriptions: RankGiftDescriptions) -> str | None:
        return rank_gift_descriptions.get_name(self.threshold)


class RankGifts:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.rank_gift = self.read_rank_gift()

    def read_rank_gift(self) -> list[RankGift] | None:
        rank_gift: list[RankGift] = []
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("DataLocal", "rankGift.csv")
        if data is None:
            return None
        csv = core.CSV(data)
        for i, line in enumerate(csv):
            rewards: list[tuple[int, int]] = []
            for col in range(1, len(line), 2):
                value = line[col].to_int()
                if value == -1:
                    break
                rewards.append((value, line[col + 1].to_int()))
            rank_gift.append(RankGift(i, line[0].to_int(), rewards))
        return rank_gift

    def get_rank_gift(self, user_rank: int) -> RankGift | None:
        if self.rank_gift is None:
            return None
        for rank_gift in self.rank_gift:
            if rank_gift.threshold == user_rank:
                return rank_gift
        return None

    def get_all_rank_gifts(self, user_rank: int) -> list[RankGift] | None:
        if self.rank_gift is None:
            return None
        return [
            rank_gift
            for rank_gift in self.rank_gift
            if rank_gift.threshold <= user_rank
        ]

    def get_by_id(self, id: int) -> RankGift | None:
        if self.rank_gift is None:
            return None
        if id >= len(self.rank_gift) or id < 0:
            return None
        return self.rank_gift[id]

    def get_all_unlocked(self, user_rank: int) -> list[RankGift] | None:
        if self.rank_gift is None:
            return None

        return [
            rank_gift
            for rank_gift in self.rank_gift
            if rank_gift.threshold <= user_rank
        ]


class RankGiftDescription:
    def __init__(self, index: int, threshold: int, description: str):
        self.index = index
        self.threshold = threshold
        self.description = description


class RankGiftDescriptions:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.rank_gift_descriptions = self.read_rank_gift_descriptions()

    def read_rank_gift_descriptions(self) -> list[RankGiftDescription] | None:
        rank_gift_descriptions: list[RankGiftDescription] = []
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("resLocal", "user_info.tsv")
        if data is None:
            return None
        csv = core.CSV(data, delimiter="\t")
        for i, line in enumerate(csv):
            rank_gift_descriptions.append(
                RankGiftDescription(i, line[0].to_int(), line[1].to_str())
            )
        return rank_gift_descriptions

    def get_name(self, user_rank: int) -> str | None:
        if self.rank_gift_descriptions is None:
            return None
        for rank_gift_description in self.rank_gift_descriptions:
            if rank_gift_description.threshold == user_rank:
                return rank_gift_description.description
        return None


class Reward:
    def __init__(self, claimed: bool):
        self.claimed = claimed

    @staticmethod
    def init() -> Reward:
        return Reward(False)

    @staticmethod
    def read(stream: core.Data) -> Reward:
        return Reward(stream.read_bool())

    def write(self, stream: core.Data):
        stream.write_bool(self.claimed)

    def serialize(self) -> bool:
        return self.claimed

    @staticmethod
    def deserialize(data: bool) -> Reward:
        return Reward(data)

    def __repr__(self) -> str:
        return f"Reward(claimed={self.claimed})"

    def __str__(self) -> str:
        return self.__repr__()


class UserRankRewards:
    def __init__(self, rewards: list[Reward]):
        self.rewards = rewards
        self.rank_gifts: RankGifts | None = None

    def read_rank_gifts(self, save_file: core.SaveFile) -> RankGifts:
        if self.rank_gifts is None:
            self.rank_gifts = RankGifts(save_file)
        return self.rank_gifts

    @staticmethod
    def init(gv: core.GameVersion) -> UserRankRewards:
        if gv >= 30:
            total = 0
        else:
            total = 50
        rewards = [Reward.init() for _ in range(total)]
        return UserRankRewards(rewards)

    @staticmethod
    def read(stream: core.Data, gv: core.GameVersion) -> UserRankRewards:
        if gv >= 30:
            total = stream.read_int()
        else:
            total = 50
        rewards: list[Reward] = []
        for _ in range(total):
            rewards.append(Reward.read(stream))
        return UserRankRewards(rewards)

    def write(self, stream: core.Data, gv: core.GameVersion):
        if gv >= 30:
            stream.write_int(len(self.rewards))
        for reward in self.rewards:
            reward.write(stream)

    def serialize(self) -> list[bool]:
        return [reward.serialize() for reward in self.rewards]

    @staticmethod
    def deserialize(data: list[bool]) -> UserRankRewards:
        return UserRankRewards([Reward.deserialize(reward) for reward in data])

    def __repr__(self) -> str:
        return f"Rewards(rewards={self.rewards})"

    def __str__(self) -> str:
        return self.__repr__()

    def set_claimed(self, index: int, claimed: bool):
        self.rewards[index].claimed = claimed
