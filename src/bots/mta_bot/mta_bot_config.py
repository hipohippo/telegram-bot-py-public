from configparser import SectionProxy
from typing import Union

import pandas as pd

from bot_common.bot_config.bot_config import BotConfig
from bot_common.util import format_white_list
from public_transit.nyc_mta.resource.load_stop_info import load_stop_info


class MTASubwayBotConfig(BotConfig):
    def __init__(self, bot_config_dict: Union[dict, SectionProxy]):
        super().__init__(
            int(bot_config_dict["heart_beat_chat"]),
            int(bot_config_dict["error_notify_chat"]),
            white_list_id=format_white_list(bot_config_dict["white_list"]),
            bot_name="MTA Subway Bot",
        )
        self.minute_departure_cap = int(bot_config_dict["minute_departure_cap"])
        self.api_key: str = bot_config_dict["api_key"]

        stop_info_df: pd.DataFrame = load_stop_info()
        stop_info_df = stop_info_df[pd.isnull(stop_info_df["parent_station"])][["stop_id", "stop_name"]]
        stop_info_df["route"] = [x[0] for x in stop_info_df["stop_id"]]
        self.stop_info_df = stop_info_df
        self.stop_id_name_map = {row["stop_id"]: row["stop_name"] for idx, row in stop_info_df.iterrows()}
