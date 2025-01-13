import logging
import sys
from configparser import SectionProxy
from typing import Union

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.channel_chat_manager_bot.bot_config import ChannelBotConfig
from bots.channel_chat_manager_bot.bot_handler import (
    add_suspicious_keyword,
    ban_user_handler,
    delete_post_handler,
    filter_handler,
    init_command_menu,
    reload_suspicious_keywords,
    reply_current_keywords,
    save_message_id_to_user_id,
)
from telegram.ext import Application, CommandHandler, MessageHandler, filters


def build_bot_app(bot_config_dict: Union[dict, SectionProxy]) -> Application:
    bot_config = ChannelBotConfig(bot_config_dict)
    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler("reload", reload_suspicious_keywords),
                CommandHandler("add", add_suspicious_keyword),
                CommandHandler("current", reply_current_keywords),
                CommandHandler("delete", delete_post_handler),
                CommandHandler("ban", ban_user_handler),
                MessageHandler(filters.ALL, filter_handler),
            ]
        )
        .add_onetime_jobs(
            [
                (init_command_menu, {"when": 1}),
            ]
        )
        .add_repeating_jobs(
            [
                (save_message_id_to_user_id, {"first": 10, "interval": 3600}),
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
    bot_config_file = sys.argv[1]
    bot_config_dict = parse_from_ini(bot_config_file)
    bot_config_dict["suspicious_keywords_file"] = sys.argv[2]
    bot_config_dict["message_id_to_user_id_file"] = sys.argv[3]
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
