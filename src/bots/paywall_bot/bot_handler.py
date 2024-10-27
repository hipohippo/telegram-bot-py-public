import asyncio
import logging

import numpy as np
from bs4 import BeautifulSoup
from nodriver.core.browser import Browser
from nodriver.core.tab import Tab
from telegram import Update, Message
from telegram.ext import ContextTypes

from bot_common.html_util.html_parse import paragraphs_to_html, extract_text_from_soup
from bot_common.telegraph_publisher.publisher import publish_single
from bot_common.util import parse_command_and_argument
from bots.paywall_bot.paywall_bot_config import PaywallBotConfig


async def unified_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (not update) or (not update.message) or (not update.message.text):
        logging.info("invalid update")
        return
    txt = update.message.text
    cmd, arg = parse_command_and_argument(txt)
    if cmd == "/p":
        telegraph_url = await paywall_handler(update, context, arg[1])
    elif cmd == "/t":
        await _translate_handler(update, context, arg[1])
    elif cmd == "/pt":
        telegraph_url = await paywall_handler(update, context, arg[1])
        await _translate_handler(update, context, telegraph_url)


async def paywall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, page_url: str):
    logging.info(f"received request for {page_url}")
    bot_config: PaywallBotConfig = context.bot_data["bot_config"]
    browser: Browser = context.bot_data["browser"]
    if not np.any([page_url.lower().find(site) >= 0 for site in bot_config.supported_sites]):
        await update.message.reply_text("website not supported yet")
        return

    telegraph_url = None
    for attempt in range(bot_config.max_attempts):
        try:
            tab: Tab = await browser.get(page_url)
            content = await tab.get_content()
            soup = BeautifulSoup(content, "html.parser")
            title, paragraphs = extract_text_from_soup(soup)
            output_html_content = paragraphs_to_html(paragraphs)
            telegraph_url = publish_single(bot_config.telegraph_publisher, title, "bot", output_html_content)
            await update.message.reply_html(text=telegraph_url)
            break
        except Exception as e:
            error_message = (
                f"failed in chat {update.effective_chat.id}: {e}. attempt {attempt + 1}/{bot_config.max_attempts}"
            )
            logging.error(error_message)
            await context.bot.send_message(bot_config.error_notify_chat, text=error_message)
            await asyncio.sleep(5)
    return telegraph_url


## _deprecated
async def _translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, telegraph_url: str):
    logging.info(f"received request to translate {telegraph_url}")
    status_message: Message = await update.message.reply_text(
        text="translating...",
    )
    bot_config: PaywallBotConfig = context.bot_data["bot_config"]
    page_index = bot_config.deepl_tab_index
    try:
        title, paragraphs = extract_content(bot_config.browser, telegraph_url)
        translated_title = deepl_bulk_translate(
            bot_config.web_driver, page_index, bot_config.translate_throttle, [title]
        )
        # TODO 200 in config
        candidates = [paragraph for paragraph in paragraphs if len(paragraph) >= 200]
        translated_paragraphs = deepl_bulk_translate(browser, page_index, bot_config.translate_throttle, candidates)
        translated_content = paragraphs_to_html(translated_paragraphs)
        translated_url = publish_single(bot_config.telegraph_publisher, translated_title, "__", translated_content)
        logging.info(f"translated and published to{translated_url}")
        await update.message.reply_html(text=translated_url)
    except Exception as e:
        translated_text = "failed to translate"
        logging.error(e)
    await status_message.delete()
