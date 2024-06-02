import itertools
import logging
from typing import List

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext._utils.types import CCT

from bot_common.keyboard.button import Button
from bot_common.keyboard.keyboard_factory import build_keyboard_markup
from bot_common.keyboard.keyed_bot_config import KeyedBotConfig


async def init_static_keyboard(context: ContextTypes.DEFAULT_TYPE):
    bot_config: KeyedBotConfig = context.bot_data["bot_config"]
    keyboard_layout: List[List[Button]] = bot_config.keyboard_layout
    buttons = list(itertools.chain(*keyboard_layout))
    bot_config.static_keyboard_markup = build_keyboard_markup(keyboard_layout)
    bot_config.callback_registry.update({button.callback_query_data for button in buttons})
    logging.getLogger(bot_config.bot_name).info("keyboard initialized")
    return


async def start_static_keyboard_handler(update: Update, context: CCT):
    await init_static_keyboard(context)
    bot_config: KeyedBotConfig = context.bot_data["bot_config"]
    if isinstance(bot_config, KeyedBotConfig) and bot_config.static_keyboard_markup:
        await update.message.reply_text("Please choose from ", reply_markup=bot_config.static_keyboard_markup)
    context.chat_data["response_message"] = None
