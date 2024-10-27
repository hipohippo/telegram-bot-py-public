# -*- coding: utf-8 -*-
import logging
import sys

from telegram.ext import Application, CommandHandler

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.paywall_bot.bot_handler import unified_command_handler
from bots.paywall_bot.paywall_bot_config import PaywallBotConfig

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def build_bot_app(bot_config_dict) -> Application:
    bot_config = PaywallBotConfig(bot_config_dict)
    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler(["p", "t"], unified_command_handler),
            ]
        )
        .build()
    )
    return bot_app


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    bot_config_dict = parse_from_ini(sys.argv[1])
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
