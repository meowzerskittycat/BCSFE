from typing import Any


from bcsfe import __app_name__, core
from bcsfe.cli import color, dialog_creator, main, prompt


def update_external_content(_: Any = None):
    """Updates external content."""

    color.color_print_key("checking_bcsfe_update", app_name=__app_name__)
    main.Main.check_update()

    print()

    color.color_print_key("updating_external_content")
    print()
    core.ExternalThemeManager.update_all_external_themes()
    core.ExternalLocaleManager.update_all_external_locales()
    core.core_data.init_data()

    print()


def manage_game_data(_: Any = None):
    cc2 = select_country()
    if cc2 is None:
        return
    cc = cc2

    should_exit = False
    while not should_exit:
        color.color_print_key("cc_game_data", cc=cc)
        items = core.GameDataGetter.get_downloaded_versions_region(cc)
        items.sort(reverse=True)
        actions = (
            dialog_creator.Actions[tuple[core.GameVersion | None, bool, bool]]
            .new()
            .add_new_raw(
                [ver.to_string() for ver in items],
                lambda i: (items[i], False, False),
            )
            .add_new_key(
                "add_version", lambda _, region=cc: (add_version(region), False, False)
            )
            .add_new_key(
                "remove_all",
                lambda _, region=cc: (
                    core.GameDataGetter.delete_region(region),
                    False,
                    False,
                ),
            )
            .add_new_key("change_cc", lambda _: (None, False, True))
            .add_new_key("exit", lambda _: (None, True, False))
        )
        resp = dialog_creator.single_select_key(actions, "select_option")
        if resp is None:
            return
        gv2, should_exit, change_cc = resp
        if change_cc:
            cc2 = select_country()
            if cc2 is None:
                return
            cc = cc2

        if gv2 is None:
            continue

        gv = gv2

        color.color_print_key(
            "gv_path",
            path=core.GameDataGetter.get_game_data_dir()
            .add(cc.get_code())
            .add(gv.to_string()),
        )

        actions = (
            dialog_creator.Actions[bool]
            .new()
            .add_new_key(
                "remove_gv", lambda _: core.GameDataGetter.delete(cc, gv) or False
            )
            .add_new_key("go_back", lambda _: False)
        )
        resp = dialog_creator.single_select_key(actions, "select_option")
        if resp is None:
            return


def add_version(cc: core.CountryCode) -> core.GameVersion | None:
    versions = core.GameDataGetter.possible_versions(cc)
    if versions is None:
        return None
    actions = (
        dialog_creator.Actions[str | None]
        .new()
        .add_new_raw(versions, lambda i: versions[i])
        .add_new_key("none", lambda _: None)
    )

    version = dialog_creator.single_select_key(
        actions,
        "select_option",
    )

    if version is None:
        return None
    version = core.GameVersion.from_string(version)
    res = core.GameDataGetter(cc, version).try_download()
    if res is False:
        return None

    return version


def select_country() -> core.CountryCode | None:
    index = prompt.choose(
        core.CountryCode.get_all_str(),
        dialog="country_code_select",
    )
    if index is None:
        return None
    return core.CountryCode.get_all()[index]


def select_country_from(ccs: list[core.CountryCode]) -> core.CountryCode | None:
    index = prompt.choose(
        [cc.get_code() for cc in ccs],
        dialog="country_code_select",
    )
    if index is None:
        return None
    return ccs[index]


def edit_bool(config: core.Config, key: core.ConfigKey):
    value = config.get_bool(key)
    color.color_print(
        config.get_full_input_localized(
            key,
            config.get_bool_text(value),
            config.get_bool_text(config.get_default(key)),
        ),
    )
    value = dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("enable", lambda _: True)
        .add_new_key("disable", lambda _: False),
        "enable_disable_dialog",
    )
    if value is None:
        return
    config.set(key, value)
    print()
    color.color_print_key(
        "config_success",
    )


def edit_int(
    config: core.Config, key: core.ConfigKey, max: prompt.MaxValue | None = None
):
    if max is None:
        max = prompt.MaxValue.i32().hide_max()
    text = config.get_full_input_localized(
        key, str(config.get_int(key)), str(config.get_default(key))
    )
    color.color_print(text)
    value = dialog_creator.edit_int_key(key.value, config.get_int(key), max)
    config.set(key, value)

    color.color_print_key(
        "config_success",
    )


def edit_game_data_repo(config: core.Config):
    text = config.get_full_input_localized(
        core.ConfigKey.GAME_DATA_REPO,
        config.get_str(core.ConfigKey.GAME_DATA_REPO),
        config.get_default(core.ConfigKey.GAME_DATA_REPO),
    )
    color.color_print(text)
    value = prompt.text("game_data_repo_dialog")
    if value is None:
        value = config.get_default(core.ConfigKey.GAME_DATA_REPO)
    color.color_print_key("validating_game_repo")
    if not value.strip().lower().startswith(("http://", "https://")):
        color.color_print_key("invalid_url")
        return
    resp = core.RequestHandler(value.strip()).get()
    if resp is None:
        color.color_print_key("no_internet_or_connection_error")
        return
    if resp.status_code != 200:
        color.color_print_key("invalid_response", response_code=resp.status_code)
        return
    config.set(core.ConfigKey.GAME_DATA_REPO, value.strip())
    color.color_print_key(
        "config_success",
    )


def edit_str(config: core.Config, key: core.ConfigKey):
    text = config.get_full_input_localized(
        key,
        config.get_str(key),
        config.get_default(key),
    )

    color.color_print(text)

    str_val = core.core_data.local_manager.get_key(key.value)

    value = prompt.text("string_config_dialog", val=str_val)
    if value is None:
        return

    config.set(key, value)
    color.color_print_key("config_success")


def add_locale(config: core.Config):
    all_locales = core.LocalManager.get_all_locales()
    if not core.GitHandler.is_git_installed():
        color.color_print_key(
            "git_not_installed",
        )
        return
    git_repo = prompt.text("enter_locale_git_repo")
    if git_repo is None or not git_repo.strip():
        color.color_print_key("locale_cancelled")
        return
    git_repo = git_repo.strip()
    external_locale = core.ExternalLocale.from_git_repo(git_repo)
    if external_locale is None:
        color.color_print_key(
            "invalid_git_repo",
        )
        return
    locale_name = external_locale.get_full_name()
    if locale_name in all_locales:
        if not prompt.confirm(
            "locale_already_exists",
            locale_name=locale_name,
        ):
            color.color_print_key(
                "locale_cancelled",
            )
            return

    external_locale.save()

    color.color_print_key(
        "locale_added",
    )
    return locale_name


def remove_locale(config: core.Config):
    all_locales = core.LocalManager.get_all_locales()
    options: list[str] = []
    for locale in all_locales:
        if locale.startswith("ext-"):
            options.append(locale)

    if not options:
        color.color_print_key(
            "no_external_locales",
        )
        return

    choices = prompt.choose_many(options, "locale_remove_dialog")
    if choices is None:
        return
    for choice in (options[i] for i in choices):
        core.LocalManager.remove_locale(choice)
        color.color_print_key(
            "locale_removed",
            locale_name=choice,
        )


def new_locale(config: core.Config) -> str | None:
    code = prompt.text("enter_locale_code")
    if code is None:
        return None
    code = code.strip()
    if not core.Config.valid_locale_code(code):
        color.color_print_key("invalid_locale_code")
        return None
    if code in core.LocalManager.get_all_locales():
        color.color_print_key("locale_code_taken", code=code)
        return None

    author = prompt.text("enter_author_name")
    if author is None:
        return None

    lang_name = prompt.text("enter_language_name_true")

    if lang_name is None:
        return None

    metadata = {
        "authors": [author],
        "name": f"{lang_name}",
    }

    path = core.LocalManager.get_locale_folder(code)

    en_path = core.LocalManager.get_locale_folder("en")

    en_path.copy(path)

    core.JsonFile.from_object(metadata).to_file(path.add("metadata.json"))

    color.color_print_key("created_locale_at", path=path)

    return code


def edit_locale(config: core.Config):
    text = config.get_full_input_localized(
        core.ConfigKey.LOCALE,
        config.get_str(core.ConfigKey.LOCALE),
        config.get_default(core.ConfigKey.LOCALE),
    )
    color.color_print(text)
    all_locales = core.LocalManager.get_all_locales()
    value = dialog_creator.single_select_key(
        dialog_creator.Actions[str | None]
        .new()
        .add_new_raw(all_locales, lambda v: all_locales[v])
        .add_new_key("add_locale", lambda _: add_locale(config))
        .add_new_key("new_locale", lambda _: new_locale(config))
        .add_new_key("remove_locale", lambda _: remove_locale(config)),
        "locale_dialog",
    )
    if value is None:
        return
    config.set(core.ConfigKey.LOCALE, value)
    color.color_print_key(
        "locale_changed",
        locale_name=value,
    )
    color.color_print_key(
        "config_success",
    )


def remove_theme(config: core.Config):
    themes = core.ThemeHandler.get_all_themes()
    options: list[str] = []
    for theme in themes:
        if theme.startswith("ext-"):
            options.append(theme)

    if not options:
        color.color_print_key(
            "no_external_themes",
        )
        return

    choices = prompt.choose_many(options, "theme_remove_dialog")
    if choices is None:
        return
    for choice in (options[i] for i in choices):
        core.ThemeHandler.remove_theme(choice)
        color.color_print_key(
            "theme_removed",
            theme_name=choice,
        )


def add_theme(config: core.Config):
    themes = core.ThemeHandler.get_all_themes()
    if not core.GitHandler.is_git_installed():
        color.color_print_key(
            "git_not_installed",
        )
        return
    git_repo = prompt.text("enter_theme_git_repo")
    if git_repo is None or not git_repo.strip():
        color.color_print_key("theme_cancelled")
        return
    git_repo = git_repo.strip()
    external_theme = core.ExternalTheme.from_git_repo(git_repo)
    if external_theme is None:
        color.color_print_key(
            "invalid_git_repo",
        )
        return
    theme_name = external_theme.get_full_name()
    if theme_name in themes:
        if not prompt.confirm(
            "theme_already_exists",
            theme_name=theme_name,
        ):
            color.color_print_key(
                "theme_cancelled",
            )
            return

    external_theme.save()

    color.color_print_key(
        "theme_added",
    )

    return theme_name


def edit_theme(config: core.Config):
    themes = core.ThemeHandler.get_all_themes()
    current_theme = config.get_str(core.ConfigKey.THEME)
    if current_theme not in themes:
        current_theme = "default"
    text = config.get_full_input_localized(
        core.ConfigKey.THEME,
        current_theme,
        config.get_default(core.ConfigKey.THEME),
    )
    color.color_print(text)
    value = dialog_creator.single_select_key(
        dialog_creator.Actions[str | None]
        .new()
        .add_new_raw(themes, lambda v: themes[v])
        .add_new_key("add_theme", lambda _: add_theme(config))
        .add_new_key("remove_theme", lambda _: remove_theme(config)),
        "theme_dialog",
    )
    if value is None:
        return
    config.set(core.ConfigKey.THEME, value)
    color.color_print_key(
        "theme_changed",
        theme_name=value,
    )


def edit_config(_: Any = None) -> None:
    config = core.core_data.config
    features = list(core.ConfigKey)

    choice = prompt.choose(
        prompt.keys([key.value for key in features]), "config_dialog"
    )
    if choice is None:
        return
    feature = features[choice]
    print()
    if isinstance(config.get(feature), bool):
        edit_bool(core.core_data.config, feature)
    elif isinstance(config.get(feature), int):
        if feature == core.ConfigKey.MAX_REQUEST_TIMEOUT:
            max = prompt.MaxValue.always_cap(1000).hide_max()
        else:
            max = None
        edit_int(core.core_data.config, feature, max)
    elif feature == core.ConfigKey.LOCALE:
        edit_locale(core.core_data.config)
    elif feature == core.ConfigKey.THEME:
        edit_theme(core.core_data.config)
    elif feature == core.ConfigKey.GAME_DATA_REPO:
        edit_game_data_repo(core.core_data.config)
    elif isinstance(config.get(feature), str):
        edit_str(core.core_data.config, feature)
    print()
