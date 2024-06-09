from configparser import SectionProxy
from typing import Union

from telegraph import Telegraph

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list


class PaywallBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="Paywall Bot",
        )
        self.telegraph_publisher = Telegraph(access_token=bot_config_dict["telegraph_token"])
        self.supported_sites = {
            "wsj",
            "nyt",
            "atlantic",
            "washingtonpost",
            "businessinsider",
            "ft.com",
            "economist",
        }  # "bloomberg" not quite well suppported - need throttle at 1min
        self.max_attempts = 4
        self.deepl_tab_index = 1
        self.translate = True
        self.translate_throttle = 3
