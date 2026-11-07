from typing import Any
import json
from bcsfe import core


class TalentOrb:
    def __init__(self, id: int, value: int):
        self.id = id
        self.value = value

    @staticmethod
    def init() -> TalentOrb:
        return TalentOrb(
            0,
            0,
        )

    @staticmethod
    def read(stream: core.Data, gv: core.GameVersion) -> TalentOrb:
        id = stream.read_short()
        if gv < 110400:
            value = stream.read_byte()
        else:
            value = stream.read_short()
        return TalentOrb(id, value)

    def write(self, stream: core.Data, gv: core.GameVersion):
        stream.write_short(self.id)
        if gv < 110400:
            stream.write_byte(self.value)
        else:
            stream.write_short(self.value)

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "value": self.value,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> TalentOrb:
        return TalentOrb(data.get("id", 0), data.get("value", 0))

    def __repr__(self):
        return f"Orb({self.id}, {self.value})"

    def __str__(self):
        return self.__repr__()


class TalentOrbs:
    def __init__(self, orbs: dict[int, TalentOrb]):
        self.orbs = orbs

    @staticmethod
    def init() -> TalentOrbs:
        return TalentOrbs({})

    @staticmethod
    def read(stream: core.Data, gv: core.GameVersion) -> TalentOrbs:
        length = stream.read_short()
        orbs: dict[int, TalentOrb] = {}
        for _ in range(length):
            orb = TalentOrb.read(stream, gv)
            orbs[orb.id] = orb
        return TalentOrbs(orbs)

    def write(self, stream: core.Data, gv: core.GameVersion):
        stream.write_short(len(self.orbs))
        for orb in self.orbs.values():
            orb.write(stream, gv)

    def serialize(self) -> list[dict[str, Any]]:
        return [orb.serialize() for orb in self.orbs.values()]

    @staticmethod
    def deserialize(data: list[dict[str, Any]]) -> TalentOrbs:
        return TalentOrbs(
            {orb.get("id", 0): TalentOrb.deserialize(orb) for orb in data}
        )

    def __repr__(self):
        return f"TalentOrbs({self.orbs})"

    def __str__(self):
        return self.__repr__()


class RawOrbInfo:
    def __init__(
        self,
        orb_id: int,
        rank_id: int,
        effect_id: int,
        value: list[int],
        target_id: int | None,
    ):
        self.orb_id = orb_id
        self.rank_id = rank_id
        self.effect_id = effect_id
        self.value = value
        self.target_id = target_id


class OrbInfo:
    def __init__(
        self,
        raw_orb_info: RawOrbInfo,
        rank: str,
        target: str | None,
        effect: str,
    ):
        self.raw_orb_info = raw_orb_info
        self.rank = rank
        self.target = target
        self.effect = effect

    @staticmethod
    def create_unknown(orb_id: int) -> OrbInfo:
        """Create an unknown OrbInfo

        Args:
            orb_id (int): The id of the orb

        Returns:
            OrbInfo: The unknown OrbInfo
        """
        return OrbInfo(
            RawOrbInfo(orb_id, 0, 0, [], 0),
            "???",
            "",
            "%@:%@",
        )


class OrbInfoList:
    equipment_data_file_name = "DataLocal/equipmentlist.json"
    grade_list_file_name = "DataLocal/equipmentgrade.csv"
    attribute_list_file_name = "resLocal/attribute_explonation.tsv"
    effect_list_file_name = "resLocal/equipment_explonation.tsv"

    def __init__(self, orb_info_list: list[OrbInfo]):
        """Initialize the OrbInfoList class

        Args:
            orb_info_list (list[OrbInfo]): The list of OrbInfo
        """
        self.orb_info_list = orb_info_list

    @staticmethod
    def create(save_file: core.SaveFile) -> OrbInfoList | None:
        """Create an OrbInfoList

        Args:
            save_file (core.SaveFile): The save file

        Returns:
            OrbInfoList | None: The OrbInfoList
        """
        gdg = core.core_data.get_game_data_getter(save_file)
        json_data_file = gdg.download_from_path(OrbInfoList.equipment_data_file_name)
        grade_list_file = gdg.download_from_path(OrbInfoList.grade_list_file_name)
        attribute_list_file = gdg.download_from_path(
            OrbInfoList.attribute_list_file_name
        )
        equipment_list_file = gdg.download_from_path(OrbInfoList.effect_list_file_name)
        if (
            json_data_file is None
            or grade_list_file is None
            or attribute_list_file is None
            or equipment_list_file is None
        ):
            return None
        raw_orbs = OrbInfoList.parse_json_data(json_data_file)
        if raw_orbs is None:
            return None
        orbs = OrbInfoList.load_names(
            raw_orbs, grade_list_file, attribute_list_file, equipment_list_file
        )
        return OrbInfoList(orbs)

    @staticmethod
    def parse_json_data(json_data: core.Data) -> list[RawOrbInfo] | None:
        """Parse the json data of the equipment

        Args:
            json_data (core.Data): The json data

        Returns:
            list[RawOrbInfo]: The list of RawOrbInfo
        """
        try:
            data: dict[str, Any] = core.JsonFile.from_data(json_data).as_object()
        except json.JSONDecodeError:
            return None
        orb_info_list: list[RawOrbInfo] = []
        for id, orb in enumerate(data["ID"]):
            grade_id = orb["gradeID"]
            content = orb["content"]
            value = orb["value"]
            attribute = orb.get("attribute")
            orb_info_list.append(RawOrbInfo(id, grade_id, content, value, attribute))
        return orb_info_list

    @staticmethod
    def load_names(
        raw_orb_info: list[RawOrbInfo],
        grade_data: core.Data,
        attribute_data: core.Data,
        effect_data: core.Data,
    ) -> list[OrbInfo]:
        """Load the names of the equipment

        Args:
            raw_orb_info (list[RawOrbInfo]): The list of RawOrbInfo
            grade_data (core.Data): Raw data of the grade list
            attribute_data (core.Data): Raw data of the attribute list
            effect_data (core.Data): Raw data of the effect list

        Returns:
            list[OrbInfo]: The list of OrbInfo
        """
        grade_csv = core.CSV(grade_data)
        attribute_tsv = core.CSV(attribute_data, "\t")
        effect_csv = core.CSV(effect_data, "\t")
        orb_info_list: list[OrbInfo] = []
        for orb in raw_orb_info:
            grade = grade_csv[orb.rank_id][3].to_str()
            effect = effect_csv[orb.effect_id][0].to_str()

            if orb.target_id is not None:
                attribute = attribute_tsv[orb.target_id][0].to_str()
            else:
                attribute = None

            orb_info_list.append(OrbInfo(orb, grade, attribute, effect))
        return orb_info_list

    def does_match_orb_str(self, str_1: str | None, str_2: str | None) -> bool:
        if str_2 == "*":
            return True

        if str_1 is None:
            return str_2 is None
        if str_2 is None:
            return False

        return str_1.lower() == str_2.lower()

    def get_orbs_from_component_fuzzy(
        self,
        grade: str,
        attribute: str | None,
        effect: str,
    ) -> list[OrbInfo]:
        """Get the OrbInfo from the components matching the first word of the effect and lowercased

        Args:
            grade (str): The grade of the orb
            attribute (str | None): The attribute of the orb. None if all
            effect (str): The effect of the orb

        Returns:
            list[OrbInfo]: The list of OrbInfo
        """
        orbs: list[OrbInfo] = []
        for orb in self.orb_info_list:
            if (
                (orb.rank.lower() == grade.lower() or grade == "*")
                and (self.does_match_orb_str(orb.target, attribute))
                and (orb.effect == effect or effect == "*")
            ):
                orbs.append(orb)
        return orbs

    def get_all_grades(self) -> list[str]:
        """Get all the grades

        Returns:
            list[str]: The list of grades
        """

        data = list(
            set([(orb.rank, orb.raw_orb_info.rank_id) for orb in self.orb_info_list])
        )

        data.sort(key=lambda id: id[1])

        return [orb[0] for orb in data]

    def get_all_attributes(self) -> list[str | None]:
        """Get all the attributes

        Returns:
            list[str]: The list of attributes
        """

        data = list(
            set(
                [
                    (orb.target, orb.raw_orb_info.target_id)
                    for orb in self.orb_info_list
                    if orb.target is not None and orb.raw_orb_info.target_id is not None
                ]
            )
        )

        data.sort(key=lambda id: id[1])

        return [orb[0] for orb in data]

    def get_all_effects(self) -> list[str]:
        """Get all the effects

        Returns:
            list[str]: The list of effects
        """

        data = list(
            set(
                [(orb.effect, orb.raw_orb_info.effect_id) for orb in self.orb_info_list]
            )
        )

        data.sort(key=lambda id: id[1])

        return [orb[0] for orb in data]


class SaveOrb:
    """Represents a saved orb in the save file"""

    def __init__(self, orb: OrbInfo, count: int):
        """Initialize the SaveOrb class

        Args:
            orb (OrbInfo): The OrbInfo
            count (int): The amount of the orb
        """
        self.count = count
        self.orb = orb
