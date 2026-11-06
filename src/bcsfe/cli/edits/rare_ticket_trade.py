from bcsfe import core

from bcsfe.cli import color, prompt


class RareTicketTrade:
    @staticmethod
    def rare_ticket_trade(save_file: core.SaveFile):
        current_amount = save_file.rare_tickets
        max_amount = max(
            core.core_data.max_value_manager.rare_tickets - current_amount,
            0,
        )
        if max_amount == 0:
            color.color_print_key("rare_ticket_trade_maxed")
            return
        to_add = prompt.number(
            "rare_ticket_trade_enter",
            max=prompt.MaxValue.i32(max_amount),
            current=current_amount,
        )
        if to_add is None:
            return

        space = False
        for storage_item in save_file.cats.storage_items:
            if storage_item.item_type == 0 or (
                storage_item.item_id == 1 and storage_item.item_type == 2
            ):
                storage_item.item_id = 1
                storage_item.item_type = 2
                space = True
                break

        if not space:
            color.color_print_key("rare_ticket_trade_storage_full")
            return

        amount = to_add * 5
        save_file.gatya.trade_progress = amount

        color.color_print_key(
            "rare_ticket_successfully_traded", rare_ticket_count=to_add
        )
