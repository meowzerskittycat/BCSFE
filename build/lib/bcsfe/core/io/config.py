import enum
import re
from typing import Any
from bcsfe import core


class ConfigKey(enum.Enum):
    LOCALE = "locale"
    SHOW_MISSING_LOCALE_KEYS = "show_missing_locale_keys"
    DISABLE_MAXES = "disable_maxes"
    MAX_BACKUPS = "max_backups"
    THEME = "theme"
    RESET_CAT_DATA = "reset_cat_data"
    SET_CAT_CURRENT_FORMS = "set_cat_current_forms"
    STRICT_UPGRADE = "strict_upgrade"
    SEPARATE_CAT_EDIT_OPTIONS = "separate_cat_edit_options"
    STRICT_BAN_PREVENTION = "strict_ban_prevention"
    MAX_REQUEST_TIMEOUT = "max_request_timeout"
    GAME_DATA_REPO = "game_data_repo"
    FORCE_LANG_GAME_DATA = "force_lang_game_data"
    CLEAR_TUTORIAL_ON_LOAD = "clear_tutorial_on_load"
    REMOVE_BAN_MESSAGE_ON_LOAD = "remove_ban_message_on_load"
    UNLOCK_CAT_ON_EDIT = "unlock_cat_on_edit"
    USE_FILE_DIALOG = "use_file_dialog"
    ADB_PATH = "adb_path"
    IGNORE_PARSE_ERROR = "ignore_parse_error"
    USE_PKEXEC_WAYDROID = "use_pkexec_waydroid"


class Config:
    def __init__(self, path: core.Path | None, print_yaml_err: bool = True):
        if path is None:
            path = Config.get_config_path()
        config = core.YamlFile(path, print_yaml_err)
        self.config: dict[ConfigKey, Any] = {}
        for key, value in config.yaml.items():
            try:
                self.config[ConfigKey(key)] = value
            except ValueError:
                pass
        self.config_object = config
        self.initialize_config()

    @staticmethod
    def get_config_path() -> core.Path:
        return core.Path.get_config_folder().add("config.yaml")

    def __getitem__(self, key: ConfigKey) -> Any:
        return self.config[key]

    def __setitem__(self, key: ConfigKey, value: Any) -> None:
        self.config[key] = value

    def __contains__(self, key: ConfigKey) -> bool:
        return key in self.config

    @staticmethod
    def get_defaults() -> dict[ConfigKey, Any]:
        initial_values = {
            ConfigKey.LOCALE: "en",
            ConfigKey.SHOW_MISSING_LOCALE_KEYS: False,
            ConfigKey.DISABLE_MAXES: False,
            ConfigKey.MAX_BACKUPS: 50,
            ConfigKey.THEME: "default",
            ConfigKey.RESET_CAT_DATA: True,
            ConfigKey.SET_CAT_CURRENT_FORMS: True,
            ConfigKey.STRICT_UPGRADE: False,
            ConfigKey.SEPARATE_CAT_EDIT_OPTIONS: True,
            ConfigKey.STRICT_BAN_PREVENTION: False,
            ConfigKey.MAX_REQUEST_TIMEOUT: 30,
            ConfigKey.GAME_DATA_REPO: "https://git.battlecatsmodding.org/fieryhenry/BCData/raw/branch/main/metadata.json",
            ConfigKey.FORCE_LANG_GAME_DATA: False,
            ConfigKey.CLEAR_TUTORIAL_ON_LOAD: True,
            ConfigKey.REMOVE_BAN_MESSAGE_ON_LOAD: True,
            ConfigKey.UNLOCK_CAT_ON_EDIT: True,
            ConfigKey.USE_FILE_DIALOG: True,
            ConfigKey.ADB_PATH: "adb",
            ConfigKey.IGNORE_PARSE_ERROR: False,
            ConfigKey.USE_PKEXEC_WAYDROID: True,
        }
        return initial_values

    def get_default(self, key: ConfigKey) -> Any:
        value = Config.get_defaults()[key]
        return value

    def set_default(self, key: ConfigKey):
        value = self.get_default(key)
        self.config[key] = value
        self.save()
        return value

    def initialize_config(self):
        initial_values = Config.get_defaults()

        for key, value in initial_values.items():
            if key not in self.config:
                self.config[key] = value
        self.save()

    def save(self):
        for key, value in self.config.items():
            self.config_object.yaml[key.value] = value
        self.config_object.save()

    def get(self, key: ConfigKey) -> Any:
        value = self.config[key]
        if value is None:
            return self.set_default(key)
        return value

    def get_game_data_repo(self, fix_old_repo: bool = True) -> str:
        if fix_old_repo and self.get_str(ConfigKey.GAME_DATA_REPO) in [
            "https://raw.githubusercontent.com/fieryhenry/BCData/master/",
            "https://git.fyhenry.uk/henry/BCData/raw/branch/main/info.json",
        ]:
            self.set(
                ConfigKey.GAME_DATA_REPO, self.get_default(ConfigKey.GAME_DATA_REPO)
            )
        return self.get_str(ConfigKey.GAME_DATA_REPO)

    def get_str(self, key: ConfigKey) -> str:
        value = self.get(key)
        if not isinstance(value, str):
            return self.set_default(key)
        return value

    def get_bool(self, key: ConfigKey) -> bool:
        value = self.get(key)
        if not isinstance(value, bool):
            return self.set_default(key)
        return value

    def get_int(self, key: ConfigKey) -> int:
        value = self.get(key)
        if not isinstance(value, int):
            return self.set_default(key)
        return value

    def reset(self):
        self.config.clear()
        self.config_object.remove()
        self.initialize_config()

    def set(self, key: ConfigKey, value: Any):
        self.config[key] = value
        self.save()

    def get_bool_text(self, value: bool) -> str:
        if value:
            return core.core_data.local_manager.get_key("enabled")
        return core.core_data.local_manager.get_key("disabled")

    def get_full_input_localized(
        self, key: ConfigKey, current_value: str, default_value: str
    ) -> str:
        return core.core_data.local_manager.get_key(
            "config_full",
            key_desc=core.core_data.local_manager.get_key(
                Config.get_desc_key(key),
                current_value=current_value,
                default_value=default_value,
                escape=False,
            ),
            escape=False,
        )

    @staticmethod
    def get_desc_key(key: ConfigKey) -> str:
        return key.value + "_desc"

    @staticmethod
    def valid_locale_code(code: str) -> bool:
        """A code is used as a folder name, so it must be one plain word."""
        return re.fullmatch(r"[A-Za-z0-9_-]+", code) is not None and not (
            code.startswith("ext-")
        )
