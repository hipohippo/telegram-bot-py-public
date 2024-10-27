from typing import Union
from configparser import SectionProxy

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list
from mastodon import Mastodon


class MastodonBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="Mastodon Bot",
        )
        self.client_id = bot_config_dict["client_id"]
        self.client_secret = bot_config_dict["client_secret"]
        self.access_token = bot_config_dict["access_token"]
        self.api_base_url = bot_config_dict["api_base_url"]
        self.mastodon_object = Mastodon(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=self.access_token,
            api_base_url=self.api_base_url,
        )
