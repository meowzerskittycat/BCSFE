from bcsfe import core


class Enemy:
    def __init__(self, id: int):
        self.id = id

    # Selections build new Enemy objects each time, so combining them (and, or)
    # has to compare ids.
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Enemy) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def unlock_enemy_guide(self, save_file: core.SaveFile):
        save_file.enemy_guide[self.id] = 1

    def reset_enemy_guide(self, save_file: core.SaveFile):
        save_file.enemy_guide[self.id] = 0

    def get_name(self, save_file: core.SaveFile) -> str | None:
        return core.core_data.get_enemy_names(save_file).get_name(self.id)


class EnemyDictionaryItem:
    def __init__(self, enemy_id: int, scale: int, first_seen: int | None):
        self.enemy_id = enemy_id
        self.scale = scale
        self.first_seen = first_seen


class EnemyDictionary:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.dictionary = self.__get_dictionary()

    def __get_dictionary(self) -> list[EnemyDictionaryItem] | None:
        gdg = core.core_data.get_game_data_getter(self.save_file)
        csv_data = gdg.download("DataLocal", "enemy_dictionary_list.csv")
        if csv_data is None:
            return None

        csv = core.CSV(csv_data)
        data: list[EnemyDictionaryItem] = []

        for row in csv:
            first_seen = None
            if len(row) >= 3:
                first_seen = row[2].to_int()
            data.append(
                EnemyDictionaryItem(row[0].to_int(), row[1].to_int(), first_seen)
            )

        return data

    def get_valid_enemies(self) -> list[int] | None:
        if self.dictionary is None:
            return None

        return [enemy.enemy_id for enemy in self.dictionary]

    def get_invalid_enemies(self, total_enemies: int) -> list[int] | None:
        valid_enemies = self.get_valid_enemies()
        if valid_enemies is None:
            return None

        valid_enemies = set(valid_enemies)

        return list(filter(lambda i: i not in valid_enemies, range(total_enemies)))


class EnemyNames:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.names = self.get_names()

    def get_names(self) -> list[str] | None:
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("resLocal", "Enemyname.tsv")
        if data is None:
            return None
        csv = core.CSV(
            data,
            "\t",
            remove_empty=False,
        )
        names: list[str] = []
        for row in csv:
            names.append(row[0].to_str())

        return names

    def get_name(self, id: int) -> str | None:
        if self.names is None:
            return None
        try:
            name = self.names[id]
            if not name:
                return core.core_data.local_manager.get_key(
                    "enemy_not_in_name_list", id=id
                )
        except IndexError:
            return core.core_data.local_manager.get_key("enemy_unknown_name", id=id)
        return name
