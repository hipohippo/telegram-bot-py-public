from pathlib import Path
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from bot_common.common_handler import send_file
from bot_common.util import restricted
from bots.book_bot.book_bot_config import BookBotConfig
from bots.book_bot.book_db import search_book_df


@restricted
async def general_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/recache":
        await recache_handler(update, context)
        return
    if update.message.text == "/allbook":
        await all_book_handler(update, context)
        return
    if "status" not in context.chat_data or context.chat_data["status"] == "READY":
        await reply_book_handler(update, context)
        return
    elif context.chat_data["status"] == "REPLIED":
        await select_from_results(update, context)
        return


@restricted
async def recache_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["status"] = "READY"
    bot_config: BookBotConfig = context.bot_data["bot_config"]
    bot_config.recache()
    await update.message.reply_text(f"recached {len(bot_config.book_df)} books")


@restricted
async def all_book_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["status"] = "READY"
    bot_config: BookBotConfig = context.bot_data["bot_config"]
    bot_config.book_df.to_excel("bdf.xlsx", encoding="utf-8")
    f = open("bdf.xlsx", "rb")
    await context.bot.send_document(update.message.chat_id, f)


@restricted
async def reply_book_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keywords: str = update.message.text
    book_files: List[Path] = search_book_df(
        keywords, context.bot_data["bot_config"].book_df
    )
    MAX_ITEMS = 20
    # await context.bot.send_message(update.message.chat_id, f"found {len(book_files)} files.")
    if len(book_files) > 0:
        context.chat_data["status"] = "REPLIED"
        context.chat_data["books_to_select"] = book_files[
            : min(len(book_files), MAX_ITEMS)
        ]
        await update.message.reply_text(
            f"found {len(context.chat_data['books_to_select'])} books\n"
            + "\n".join(
                [
                    f"{i + 1}. {book_file.name}"
                    for i, book_file in enumerate(context.chat_data["books_to_select"])
                ]
            )
        )
        return
    else:
        await update.message.reply_text("No book found")
        return


@restricted
async def select_from_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        selected_book_number = int(update.message.text)
    except:
        await update.message.reply_text(
            "Invalid selection. Type 0 to exit and start a new search"
        )
        return
    if 1 <= selected_book_number <= len(context.chat_data["books_to_select"]):
        book_file: Path = context.chat_data["books_to_select"][selected_book_number - 1]
        await update.message.reply_text(book_file.name)
        await send_file(book_file, update, context)
    else:
        context.chat_data["status"] = "READY"
        context.chat_data["books_to_select"] = []
        await update.message.reply_text("Reset Search Done")
