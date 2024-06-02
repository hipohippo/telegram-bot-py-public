from typing import List, Optional, Union

from telegram import InlineKeyboardMarkup

from bot_common.bot_config.bot_config import BotConfig
from bot_common.keyboard.button import Button


class KeyedBotConfig(BotConfig):
    def __init__(
        self,
        heart_beat_chat: Union[int, str],
        error_notify_chat: Union[int, str],
        white_list_id: Optional[List[int]],
        bot_name: str,
        keyboard_layout: List[List[Button]],
    ):
        super().__init__(heart_beat_chat, error_notify_chat, white_list_id, bot_name)
        self._keyboard_layout = keyboard_layout
        self._static_keyboard_markup = None
        self.callback_registry = set()

    @property
    def keyboard_layout(self):
        return self._keyboard_layout

    @property
    def static_keyboard_markup(self):
        return self._static_keyboard_markup

    @static_keyboard_markup.setter
    def static_keyboard_markup(self, value: InlineKeyboardMarkup):
        self._static_keyboard_markup = value
