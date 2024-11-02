import logging
import sys

from telegram.ext import CommandHandler, Application

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bot_common.common_handler import init_browser_handler
from bots.njt_bot.bot_handler import next_bus_handler, init_cmd, lightrail_alert_handler, path_handler
from bots.njt_bot.njt_bot_config import NJTBotConfig
from public_transit.njtransit.query.path import PathStation


def build_bot_app(bot_config_dict) -> Application:
    bot_config = NJTBotConfig(bot_config_dict)
    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler("homeny", next_bus_handler),
                CommandHandler("homenj", next_bus_handler),
                CommandHandler("pabt", next_bus_handler),
                CommandHandler("lr", lightrail_alert_handler),
                CommandHandler(set(PathStation.get_station_map().keys()), path_handler),
            ]
        )
        .add_onetime_jobs([(init_cmd, {"when": 2}), (init_browser_handler, {"when": 1})])
        .build()
    )

    return bot_app


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    bot_config_file = sys.argv[1]
    bot_config_dict = parse_from_ini(bot_config_file)
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
