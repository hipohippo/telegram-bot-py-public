import logging
import sys

from telegram.ext import CommandHandler, Application

from bot_common.bot_config.bot_config_parser import parse_from_ini
from bot_common.bot_controller.bot_controller_config import BotControllerConfig
from bot_common.bot_controller.handler import (
    start_bot_handler,
    stop_bot_handler,
    test_handler,
    stop_all_handler,
    exit_handler,
    list_active_handler,
    list_all_handler,
    restart_all_handler,
)
from bot_common.bot_factory import BotBuilder
from bot_common.util import section_proxy_to_dict


def build_bot_app(bot_config_dict) -> Application:
    bot_config = BotControllerConfig(bot_config_dict)
    bot_app = (
        BotBuilder(bot_config_dict["bot_token"], bot_config)
        .add_handlers(
            [
                CommandHandler("start", start_bot_handler),
                CommandHandler("list", list_active_handler),
                CommandHandler("all", list_all_handler),
                CommandHandler("stop", stop_bot_handler),
                CommandHandler("stopall", stop_all_handler),
                CommandHandler("restartall", restart_all_handler),
                CommandHandler("exit", exit_handler),
                CommandHandler("test", test_handler),
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
    bot_config_dict = section_proxy_to_dict(parse_from_ini(bot_config_file))
    bot_config_dict.update(
        {"exec_script": parse_from_ini(bot_config_file, section="exec_script")}
    )
    bot_app = build_bot_app(bot_config_dict)
    bot_app.bot_data["exec_pid"] = dict()
    bot_app.run_polling()
