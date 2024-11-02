from pathlib import Path

import nodriver as uc
import pandas as pd
from nodriver.core.browser import Browser
from telegram import Update
from telegram.ext import ContextTypes

from bot_common.bot_config.bot_config import BotConfig


# handlers will be applied in the order defined...if accepted by one handler, it will stop processing more rules
# https://stackoverflow.com/questions/77034884/how-to-make-my-telegram-bots-handler-not-block-each-other


async def heart_beat_job(context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotConfig = context.bot_data["bot_config"]
    active = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M")
    # bot_config.redis_conn.hmset(bot_config.bot_name, {"last_active": active})

    await context.bot.send_message(
        chat_id=bot_config.heart_beat_chat,
        text=f"heart beat from {bot_config.bot_name} at {active} UTC",
    )


async def poke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message.text.split(" ")[0] == "/poke"
    await update.message.reply_text("poke back")


async def error_notification_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotConfig = context.bot_data["bot_config"]
    await context.bot.send_message(chat_id=bot_config.error_notify_chat)


async def send_file(file: Path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (not file) or (not file.is_file()):
        await update.message.reply_text("file invalid")
        return
    elif file.stat().st_size <= 49 * 0x100000:  # up to 49MB
        status_message = await update.message.reply_text("uploading")
        with open(file, "rb") as doc:
            await context.bot.send_document(update.message.chat_id, doc)
        await status_message.delete()
        return
    else:
        await update.message.reply_text("file found but too large, exceeding threshold of 50MB.")
        return


async def init_browser_handler(context: ContextTypes.DEFAULT_TYPE):
    browser: Browser = await uc.start()
    context.bot_data["browser"] = browser
    return
