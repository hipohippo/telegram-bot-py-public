import logging
import sys

from telegram.ext import Application, MessageHandler, filters

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_factory import BotBuilder
from bots.neodb_bot.neodb_bot_config import NeoDBBotConfig

# from bots.neodb_bot.bot_handler import search_handler, mark_progress_handler
from bots.neodb_bot.conversation_handler import (
    start_search,
    search_items,
    select_item,
    perform_action,
    cancel,
    SEARCH,
    SELECT_ITEM,
    CHOOSE_ACTION,
)
from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler



def build_bot_app(bot_config_dict) -> Application:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    bot_config = NeoDBBotConfig(bot_config_dict)

    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        # .add_handlers(
        #   [
        #      MessageHandler(filters.Regex(r"^[Ss] .+"), search_handler),
        #      MessageHandler(filters.Regex(r"^[Mm] .+"), mark_progress_handler),
        #  ]
        # )  # handlers will be applied in the order defined...if accepted by one handler, it will stop processing more rules
        .add_handlers(
            [
                ConversationHandler(
                    entry_points=[CommandHandler("search", start_search)],
                    states={
                        SEARCH: [
                            MessageHandler(
                                filters.TEXT & ~filters.COMMAND, search_items
                            )
                        ],
                        SELECT_ITEM: [CallbackQueryHandler(select_item)],
                        CHOOSE_ACTION: [CallbackQueryHandler(perform_action)],
                    },
                    fallbacks=[CommandHandler("cancel", cancel)],
                )
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
    bot_config_dict = parse_from_ini(sys.argv[1])
    bot_app = build_bot_app(bot_config_dict)
    bot_app.run_polling()
