from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot_common.keyboard.button import Button


def build_keyboard_markup(keyboard_layout: List[List[Button]]) -> InlineKeyboardMarkup:
    """
    keyboard is a 2-dim list, each element represents a line
    keyboard_markup builds upon keyboard
    :return:
    """

    keyboard: List[List[InlineKeyboardButton]] = []
    for level in keyboard_layout:
        keyboard.append(
            [
                InlineKeyboardButton(
                    button.display_name, callback_data=button.callback_query_data
                )
                for button in level
            ]
        )
    keyboard_markup = InlineKeyboardMarkup(keyboard)
    return keyboard_markup
