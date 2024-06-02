from configparser import SectionProxy
from typing import Union

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list


class NJTBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="NJT Next Bus Bot",
        )
