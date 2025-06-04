from configparser import SectionProxy
from pathlib import Path
from typing import Union

import pandas as pd

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list
from bots.book_bot.book_db import init_df


class BookBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="Hipo Book Bot",
        )
        self.book_path: Path = Path(bot_config_dict["book_folder_path"])
        self.boox_url: str = bot_config_dict["boox_url"]
        self.recache()

    @staticmethod
    def validate_book_df(book_df: pd.DataFrame):
        """Validate that book_df has the required columns"""
        required_columns = {"name", "fullpath", "category"}
        missing_columns = required_columns - set(book_df.columns)
        if missing_columns:
            raise ValueError(
                f"Book DataFrame is missing required columns: {missing_columns}"
            )

    def recache(self):
        self.book_df = init_df(self.book_path)
        self.validate_book_df(self.book_df)
