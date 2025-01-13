import logging
from configparser import SectionProxy
from typing import List, Union

import pandas as pd
from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list


class ChannelBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="Channel-Manager-Bot",
        )
        self.managed_channels = self._parse_channels(
            bot_config_dict["managed_channels"]
        )
        self.managed_channel_groups = self._parse_channels(
            bot_config_dict["managed_channel_groups"]
        )
        self.suspicious_keywords_file = bot_config_dict["suspicious_keywords_file"]
        self.suspicious_keywords = self._parse_suspicious_keywords(
            self.suspicious_keywords_file
        )
        logging.getLogger(__name__).info(
            f"Suspicious keywords: {self.suspicious_keywords}"
        )

        self.message_id_to_user_id_file = bot_config_dict["message_id_to_user_id_file"]
        self.message_id_to_user_id = pd.read_csv(self.message_id_to_user_id_file)

    @staticmethod
    def _parse_channels(channels_str: str) -> List[int]:
        if not channels_str:
            return []
        return [int(channel_id) for channel_id in channels_str.split(",") if channel_id]

    @staticmethod
    def _parse_suspicious_keywords(file_name: str) -> List[str]:
        with open(file_name, "r") as file:
            return [line.strip() for line in file.readlines()]
