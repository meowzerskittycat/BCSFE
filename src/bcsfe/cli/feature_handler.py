"""The main menu: a tree of feature categories, searchable by name.

Numbers pick an entry (0 goes back), text searches every feature, and an
empty answer lists all of them. After a feature runs the menu stays in the
same category. Each feature that changes the save can be undone, and one
that fails or is cancelled with Ctrl+C leaves the save as it was.
"""

import os
import traceback
from collections.abc import Callable
from typing import Any

from bcsfe import __version__, core
from bcsfe.cli import color, edits, main, save_management

# How many edits "Undo last edit" can step back through.
MAX_UNDO = 10

type Path = tuple[str, ...]


class FeatureHandler:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        # (feature key, save bytes before it ran, country code), newest last.
        self.undo_stack: list[tuple[str, bytes, core.CountryCode]] = []

    def get_features(self) -> dict[str, Any]:
        cat_features = {"cats": edits.cat_editor.CatEditor.edit_cats}
        if core.core_data.config.get_bool(core.ConfigKey.SEPARATE_CAT_EDIT_OPTIONS):
            cat_features = {
                "unlock_remove_cats": edits.cat_editor.CatEditor.unlock_remove_cats_run,
                "upgrade_cats": edits.cat_editor.CatEditor.upgrade_cats_run,
                "true_form_remove_form_cats": edits.cat_editor.CatEditor.true_form_remove_form_cats_run,
                "force_true_form_cats": edits.cat_editor.CatEditor.force_true_form_cats_run,
                "fourth_form_remove_form_cats": edits.cat_editor.CatEditor.fourth_form_remove_form_cats_run,
                "force_fourth_form_cats": edits.cat_editor.CatEditor.force_fourth_form_cats_run,
                "upgrade_talents_remove_talents_cats": edits.cat_editor.CatEditor.upgrade_talents_remove_talents_cats_run,
                "unlock_remove_cat_guide": edits.cat_editor.CatEditor.unlock_cat_guide_remove_guide_run,
            }

        cat_features["special_skills"] = (
            edits.basic_items.BasicItems.edit_special_skills
        )

        cat_features["cat_storage"] = edits.storage.edit_storage

        features: dict[str, Any] = {
            "save_management": {
                "save_save": save_management.SaveManagement.save_save,
                "save_upload": save_management.SaveManagement.save_upload,
                "save_save_file": save_management.SaveManagement.save_save_dialog,
                core.localize(
                    "save_save_documents", path=core.SaveFile.get_save_path()
                ): save_management.SaveManagement.save_save_data_dir,
                "adb_push": save_management.SaveManagement.adb_push,
                "adb_push_rerun": save_management.SaveManagement.adb_push_rerun,
                "root_push": save_management.SaveManagement.root_push,
                "root_push_rerun": save_management.SaveManagement.root_push_rerun,
                "export_save": save_management.SaveManagement.export_save,
                "load_save": save_management.SaveManagement.load_save,
                # "init_save": save_management.SaveManagement.init_save,
                "convert_region": save_management.SaveManagement.convert_save_cc,
                "convert_version": save_management.SaveManagement.convert_save_gv,
            },
            "items": {
                "catfood": edits.basic_items.BasicItems.edit_catfood,
                "xp": edits.basic_items.BasicItems.edit_xp,
                "normal_tickets": edits.basic_items.BasicItems.edit_normal_tickets,
                "rare_tickets": edits.basic_items.BasicItems.edit_rare_tickets,
                "rare_ticket_trade_feature_name": edits.rare_ticket_trade.RareTicketTrade.rare_ticket_trade,
                "platinum_tickets": edits.basic_items.BasicItems.edit_platinum_tickets,
                "legend_tickets": edits.basic_items.BasicItems.edit_legend_tickets,
                "platinum_shards": edits.basic_items.BasicItems.edit_platinum_shards,
                "np": edits.basic_items.BasicItems.edit_np,
                "leadership": edits.basic_items.BasicItems.edit_leadership,
                "battle_items": edits.basic_items.BasicItems.edit_battle_items,
                "battle_items_endless": edits.basic_items.BasicItems.edit_battle_items_endless,
                "catseyes": edits.basic_items.BasicItems.edit_catseyes,
                "catfruit": edits.basic_items.BasicItems.edit_catfruit,
                "talent_orbs": edits.talent_orbs.SaveOrbs.edit_talent_orbs,
                "catamins": edits.basic_items.BasicItems.edit_catamins,
                "scheme_items": edits.basic_items.BasicItems.edit_scheme_items,
                "labyrinth_medals": edits.basic_items.BasicItems.edit_labyrinth_medals,
                "100_million_tickets": edits.basic_items.BasicItems.edit_100_million_ticket,
                "event_tickets": edits.event_tickets.EventTickets.edit,
                "treasure_chests": edits.basic_items.BasicItems.edit_treasure_chests,
                "reset_golden_cat_cpus": edits.basic_items.BasicItems.reset_golden_cat_cpus,
            },
            "cats_special_skills": cat_features,
            "levels": {
                "clear_tutorial": edits.clear_tutorial.clear_tutorial,
                "clear_story": edits.story.clear_story,
                "challenge_score": edits.stages.edit_challenge_score,
                "dojo_score": edits.stages.edit_dojo_score,
                "add_enigma_stages": edits.stages.edit_enigma,
                "clear_enigma_stages": edits.stages.edit_enigma_stages,
                "unlock_aku_realm": edits.aku_realm.unlock_aku_realm,
                "story_treasures": edits.story.edit_treasures,
                "outbreaks": edits.stages.edit_outbreaks,
                "aku_chapters": edits.stages.edit_aku_chapters,
                "itf_timed_scores": edits.story.edit_itf_timed_scores,
                "filibuster_reclearing": edits.basic_items.BasicItems.allow_filibuster_stage_reclearing,
                "sol": edits.map.edit_sol_chapters,
                "event": edits.map.edit_event_chapters,
                "collab": edits.map.edit_collab_chapters,
                "gauntlets": edits.stages.edit_gauntlets,
                "collab_gauntlets": edits.stages.edit_collab_gauntlets,
                "uncanny": edits.stages.edit_uncanny,
                "catamin_stages": edits.stages.edit_catamin_stages,
                "behemoth_culling": edits.stages.edit_behemoth_culling,
                "legend_quest": edits.stages.edit_legend_quest,
                "towers": edits.stages.edit_towers,
                "zero_legends": edits.stages.edit_zero_legends,
                "dojo_catclaw_championships": edits.stages.edit_catclaw_championships,
            },
            "gamototo": {
                "engineers": edits.basic_items.BasicItems.edit_engineers,
                "base_materials": edits.basic_items.BasicItems.edit_base_materials,
                "gamatoto_xp_level": edits.gamatoto.edit_xp,
                "gamatoto_helpers": edits.gamatoto.edit_helpers,
                "ototo_cat_cannon": edits.ototo.edit_cannon,
                "cat_shrine": edits.cat_shrine.edit_catshrine,
            },
            "account": {
                "unban_account": save_management.SaveManagement.unban_account,
                "upload_items": save_management.SaveManagement.upload_items,
                "inquiry_code": edits.basic_items.BasicItems.edit_inquiry_code,
                "password_refresh_token": edits.basic_items.BasicItems.edit_password_refresh_token,
            },
            "gatya": {
                "rare_gatya_seed": edits.basic_items.BasicItems.edit_rare_gatya_seed,
                "normal_gatya_seed": edits.basic_items.BasicItems.edit_normal_gatya_seed,
                "event_gatya_seed": edits.basic_items.BasicItems.edit_event_gatya_seed,
            },
            "fixes": {
                "fix_gamatoto_crash": edits.fixes.Fixes.fix_gamatoto_crash,
                "fix_ototo_crash": edits.fixes.Fixes.fix_ototo_crash,
                "fix_time_errors": edits.fixes.Fixes.fix_time_errors,
                "unlock_equip_menu": edits.basic_items.BasicItems.unlock_equip_menu,
                "fix_officer_pass_crash": edits.other.fix_officer_pass_crash,
            },
            "other": {
                "unlocked_slots": edits.basic_items.BasicItems.edit_unlocked_slots,
                "reset_gambling_events": edits.other.reset_gambling_events,
                "restart_pack": edits.basic_items.BasicItems.set_restart_pack,
                "special_skills": edits.basic_items.BasicItems.edit_special_skills,
                "playtime": edits.other.edit_playtime,
                "enemy_guide": edits.enemy_editor.EnemyEditor.edit_enemy_guide,
                "user_rank_rewards": edits.other.edit_user_rank_rewards,
                "unlock_equip_menu": edits.basic_items.BasicItems.unlock_equip_menu,
                "gold_pass": edits.other.edit_gold_pass,
                "medals": edits.other.edit_medals,
                "missions": edits.other.edit_missions,
            },
            "editor": {
                "config": edits.settings.edit_config,
                "update_external": edits.settings.update_external_content,
                "manage_game_data": edits.settings.manage_game_data,
            },
            "undo_last_edit": self.undo_last_edit,
            "exit": main.Main.exit_editor,
        }
        return features

    def get_feature(self, feature_path: list[str] | Path) -> Any:
        feature: Any = self.get_features()
        for key in feature_path:
            feature = feature[key]
        return feature

    # --- names and search ----------------------------------------------

    @staticmethod
    def aliases(key: str) -> list[str]:
        return core.core_data.local_manager.get_all_aliases(core.localize(key))

    def name(self, key: str) -> str:
        if key == "undo_last_edit" and self.undo_stack:
            return f"{self.aliases(key)[0]} ({len(self.undo_stack)})"
        return self.aliases(key)[0]

    def label(self, path: Path) -> str:
        return ": ".join(self.name(key) for key in path)

    def all_features(self, tree: dict[str, Any] | None = None) -> list[Path]:
        """Every runnable feature, depth first, in menu order."""
        if tree is None:
            tree = self.get_features()
        paths: list[Path] = []
        for key, value in tree.items():
            if isinstance(value, dict):
                paths.extend((key, *sub) for sub in self.all_features(value))  # type: ignore[arg-type]
            else:
                paths.append((key,))
        return paths

    def search_features(self, query: str) -> list[Path]:
        """Features whose name (or an alias) matches `query`, best first.

        Spaces and case are ignored. Exact names rank above names starting
        with the query, which rank above names containing it.
        """
        query = query.lower().replace(" ", "")
        ranked: list[tuple[int, int, Path]] = []
        for i, path in enumerate(self.all_features()):
            best = 0
            for alias in self.aliases(path[-1]):
                alias = alias.lower().replace(" ", "")
                if alias == query:
                    best = max(best, 3)
                elif alias.startswith(query):
                    best = max(best, 2)
                elif query in alias:
                    best = max(best, 1)
            if best:
                ranked.append((-best, i, path))
        ranked.sort()
        return [path for *_, path in ranked]

    def is_exact(self, path: Path, query: str) -> bool:
        query = query.lower().replace(" ", "")
        return any(
            alias.lower().replace(" ", "") == query for alias in self.aliases(path[-1])
        )

    # --- the menu --------------------------------------------------------

    def show(self, title: str, entries: list[str], back: bool):
        print()
        color.color_print(f"<@t>{title}</>")
        if back:
            color.color_print(f" 0. <@t>{core.localize('go_back')}</>")
        for i, entry in enumerate(entries, 1):
            color.color_print(f" {i}. <@t>{entry}</>")
        print()

    def pick(self, paths: list[Path], title: str) -> Path | None:
        """Let the user pick one of `paths` by number; blank or 0 cancels."""
        self.show(title, [self.label(path) for path in paths], back=True)
        answer = color.color_input_key("select_feature_number").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(paths):
            return paths[int(answer) - 1]
        if answer not in ("", "0"):
            color.color_print_key("invalid_input")
        return None

    def ask(self, path: Path) -> tuple[Path, Path | None]:
        """Show the category at `path` and read one answer.

        Returns the category to show next and a feature to run, if any.
        """
        tree: dict[str, Any] = self.get_feature(path) if path else self.get_features()
        keys = list(tree.keys())
        title = self.label(path) if path else core.localize("features")
        self.show(title, [self.name(key) for key in keys], back=bool(path))
        answer = color.color_input_key("select_features").strip()

        if answer.isdigit():
            number = int(answer)
            if number == 0 and path:
                return path[:-1], None
            if not 1 <= number <= len(keys):
                color.color_print_key("invalid_input")
                return path, None
            chosen = (*path, keys[number - 1])
            if isinstance(tree[keys[number - 1]], dict):
                return chosen, None
            return path, chosen

        if not answer:
            return path, self.pick(self.all_features(), core.localize("all_features"))

        found = self.search_features(answer)
        if not found:
            color.color_print_key("no_feature_with_name", name=answer)
            return path, None
        exact = [p for p in found if self.is_exact(p, answer)]
        if len(found) == 1 or len(exact) == 1:
            return path, (exact or found)[0]
        title = core.localize("feature_search_results", query=answer)
        return path, self.pick(found, title)

    def select_features_run(self):
        edits.clear_tutorial.clear_tutorial(self.save_file, False)
        self.save_file.show_ban_message = False
        self.write_temp(self.snapshot())

        path: Path = ()
        while True:
            try:
                path, feature = self.ask(path)
            except KeyboardInterrupt:
                main.Main.exit_editor(self.save_file)
            if feature is not None:
                self.run(feature)

    def run(self, path: Path):
        feature: Callable[[core.SaveFile], Any] = self.get_feature(path)
        self.do_save_actions()
        before = self.snapshot()
        cc = self.save_file.cc
        try:
            feature(self.save_file)
        except KeyboardInterrupt:
            print()
            self.restore(before, cc)
            color.color_print_key("feature_cancelled")
        except Exception as e:
            self.restore(before, cc)
            color.color_print_key(
                "feature_failed",
                error=e,
                version=__version__,
                traceback=traceback.format_exc(),
            )
        else:
            after = self.snapshot()
            if path[-1] != "undo_last_edit" and before is not None and after != before:
                self.undo_stack.append((path[-1], before, cc))
                del self.undo_stack[:-MAX_UNDO]
            self.write_temp(after)
        # Forget the game data so an updated version is downloaded next time.
        core.core_data.game_data_getter = None

    # --- snapshots, undo and the crash backup ------------------------------

    def snapshot(self) -> bytes | None:
        try:
            return self.save_file.to_data().to_bytes()
        except Exception:
            return None

    def restore(self, data: bytes | None, cc: core.CountryCode):
        if data is not None:
            self.save_file.load_save_file(core.SaveFile(core.Data(data), cc))

    @staticmethod
    def write_temp(data: bytes | None):
        """Keep a copy of the save for recovery if the editor crashes.

        Written to a side file and then renamed, so the copy is never seen
        half-written.
        """
        if data is None:
            return
        path = core.SaveFile.get_temp_path().path
        try:
            with open(path + ".part", "wb") as f:
                f.write(data)
            os.replace(path + ".part", path)
        except OSError:
            pass

    def undo_last_edit(self, save_file: core.SaveFile):
        if not self.undo_stack:
            color.color_print_key("undo_nothing")
            return
        key, before, cc = self.undo_stack.pop()
        self.restore(before, cc)
        color.color_print_key(
            "undo_success", feature=self.aliases(key)[0], remaining=len(self.undo_stack)
        )

    def do_save_actions(self):
        if core.core_data.config.get_bool(core.ConfigKey.CLEAR_TUTORIAL_ON_LOAD):
            edits.clear_tutorial.clear_tutorial(self.save_file, False)
        if core.core_data.config.get_bool(core.ConfigKey.REMOVE_BAN_MESSAGE_ON_LOAD):
            self.save_file.show_ban_message = False
