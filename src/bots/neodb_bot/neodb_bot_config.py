from typing import Union
from configparser import SectionProxy

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list
from neodb.neodb import NeoDB


class NeoDBBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="NeoDB Bot",
        )
        self.neodb_api_key = bot_config_dict["neodb_api_key"]
        self.max_item_per_query = int(bot_config_dict["max_item_per_query"])
        self.neodb_object = NeoDB(self.neodb_api_key)
        self.subkeys = {
            "book": [
                "title",
                "author",
                "isbn",
                "subtitle",
                "pub_house",
                "pub_year",
                "uuid",
            ],
            "movie": ["title", "director", "actor", "pub_house", "pub_year", "uuid"],
            "tv": ["title", "director", "actor", "pub_house", "pub_year", "uuid"],
            "music": ["title", "artist", "album", "pub_house", "pub_year", "uuid"],
            "game": [
                "title",
                "developer",
                "publisher",
                "pub_house",
                "pub_year",
                "uuid",
            ],
            "software": [
                "title",
                "developer",
                "publisher",
                "pub_house",
                "pub_year",
                "uuid",
            ],
            "other": ["title", "pub_house", "pub_year", "uuid"],
        }  # TODO: add more subkeys
