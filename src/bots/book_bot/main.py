import logging
import sys
from configparser import SectionProxy
from typing import Union

from telegram.ext import Application

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.book_bot.book_bot_config import BookBotConfig
from bots.book_bot.handler import book_conv_handler


def build_bot_app(bot_config_dict: Union[dict, SectionProxy]) -> Application:
    bot_config = BookBotConfig(bot_config_dict)
    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                book_conv_handler,
            ]
        )
        .build()
    )
    return bot_app


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    bot_app = build_bot_app(parse_from_ini(sys.argv[1]))
    bot_app.run_polling()
