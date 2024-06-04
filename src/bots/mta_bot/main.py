import logging
import sys

from telegram.ext import CommandHandler, Application, MessageHandler, filters

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.mta_bot.bot_handler import next_train_handler, show_stop_id_handler, search_stop_handler
from bots.mta_bot.mta_bot_config import MTASubwayBotConfig


def build_bot_app(bot_config_dict) -> Application:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    bot_config = MTASubwayBotConfig(bot_config_dict)

    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler("stop", show_stop_id_handler),
                MessageHandler(filters.Regex(r"^[Ss]\w$"), show_stop_id_handler),
                MessageHandler(filters.Regex(r"^[Ss] .+"), search_stop_handler),
                MessageHandler(filters.Regex(r"^\w\d{2}[NSUDnsud]$"), next_train_handler),
                MessageHandler(filters.Regex("^[rR]$"), next_train_handler),
            ]
        )  # handlers will be applied in the order defined...if accepted by one handler, it will stop processing more rules
        .build()
    )
    return bot_app


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    bot_config_dict = parse_from_ini(sys.argv[1])
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
