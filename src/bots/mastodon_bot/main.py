import logging
import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.mastodon_bot.mastodon_bot_config import MastodonBotConfig
from bots.mastodon_bot.bot_handler import post_to_mastodon


def build_bot_app(bot_config_dict) -> Application:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    bot_config = MastodonBotConfig(bot_config_dict)

    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO) & ~filters.COMMAND, post_to_mastodon
                ),
            ]
        )
        .build()
    )

    # Add Mastodon client to bot_data for easy access in handlers
    bot_app.bot_data["config"] = bot_config
    return bot_app


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    bot_config_dict = parse_from_ini(sys.argv[1])
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
