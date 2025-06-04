import logging
from pathlib import Path
from typing import List

import requests
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot_common.common_handler import send_file
from bot_common.util import restricted
from bots.book_bot.book_bot_config import BookBotConfig
from bots.book_bot.book_db import search_book_df


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("""
    Use /search <keywords> to search for a book or /s <keywords> to search for a book.
    Use /cancel to cancel the current search.
    """)


async def random_book_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a random book to the user."""
    RANDOM_BOOKS = 10
    category = context.args[0] if context.args else None
    book_df = context.bot_data["bot_config"].book_df
    if category:
        random_books: list[Path] = (
            book_df[book_df["category"] == category]
            .sample(RANDOM_BOOKS)["fullpath"]
            .tolist()
        )
    else:
        random_books: list[Path] = book_df.sample(RANDOM_BOOKS)["fullpath"].tolist()
    await update.message.reply_text(
        f"Here are {RANDOM_BOOKS} random books:\n"
        + "\n".join(f"{i + 1}. {book.name}" for i, book in enumerate(random_books))
    )
    context.user_data["search_results"] = random_books
    return SELECT_ACTION


# Define states
SEARCH, SELECT_ACTION, READY_TO_DELIVER = range(3)


@restricted
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    if not context.args:
        await update.message.reply_text("Please enter keywords to search for a book:")
        context.user_data["search_method"] = "reply"
        return SEARCH
    else:
        # Join arguments into search keywords
        context.user_data["search_keywords"] = " ".join(context.args)
        context.user_data["search_method"] = "command"
        return await search_books(update, context)


@restricted
async def search_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Search for books based on keywords and show results."""
    keywords = (
        context.user_data["search_keywords"]
        if context.user_data["search_method"] == "command"
        else update.message.text
    )
    book_files: List[Path] = search_book_df(
        keywords, context.bot_data["bot_config"].book_df
    )

    if not book_files:
        await update.message.reply_text(
            "No books found. Please try again with different keywords."
        )
        return ConversationHandler.END

    MAX_ITEMS = 20
    results: list[Path] = book_files[: min(len(book_files), MAX_ITEMS)]

    # Store results for later use
    context.user_data["search_results"] = results

    # Display numbered list of results
    result_text = "Found these books:\n" + "\n".join(
        f"{i + 1}. {book.name}" for i, book in enumerate(results)
    )

    await update.message.reply_text(
        f"{result_text}\n\nPlease enter the number of the book you want to select (1-{len(results)}):"
    )

    return SELECT_ACTION


@restricted
async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's selection of a book by index."""
    try:
        selection = int(update.message.text)
        results: list[Path] = context.user_data["search_results"]

        if selection == 0:
            await update.message.reply_text("Cancelled")
            return ConversationHandler.END

        if not (1 <= selection <= len(results)):
            await update.message.reply_text(
                f"Please enter a valid number between 1 and {len(results)}"
            )
            return SELECT_ACTION

        # Store selected book and show delivery options
        context.user_data["selected_book"] = results[selection - 1]
        await update.message.reply_text(
            "How would you like to receive the book?",
            reply_markup=ReplyKeyboardMarkup(
                [["Send to chat", "Send to Boox"]], one_time_keyboard=True
            ),
        )
        return READY_TO_DELIVER

    except ValueError:
        await update.message.reply_text("Please enter a valid number")
        return SELECT_ACTION


@restricted
async def send_to_boox_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, selected_book: Path
) -> None:
    """Send the selected book to Boox."""
    bot_config: BookBotConfig = context.bot_data["bot_config"]
    try:
        with open(selected_book, "rb") as f:
            filename = selected_book.name
            # Check for ISBN pattern at start (13 or 10 digits followed by underscore)
            if len(filename) > 14 and filename[:13].isdigit() and filename[13] == "_":
                # Move 13 digit ISBN to end
                filename = filename[14:] + "_" + filename[:13]
            elif len(filename) > 11 and filename[:10].isdigit() and filename[10] == "_":
                # Move 10 digit ISBN to end
                filename = filename[11:] + "_" + filename[:10]
            files = {"file": (filename, f)}

            response = requests.post(bot_config.boox_url, files=files)
            logging.getLogger(__name__).info(
                f"Status Code: {response.status_code}, Response: {response.text}"
            )
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error sending to Boox: {e}")
        await update.message.reply_text(
            "Error sending to Boox", reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END


@restricted
async def handle_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the delivery method for the selected book."""
    choice = update.message.text
    selected_book: Path = context.user_data["selected_book"]

    if choice not in ["Send to chat", "Send to Boox"]:
        await update.message.reply_text(
            "Please select a valid option.",
            reply_markup=ReplyKeyboardMarkup(
                [["Send to chat", "Send to Boox"]], one_time_keyboard=True
            ),
        )
        return READY_TO_DELIVER

    if choice == "Send to chat":
        # Send the file directly in chat
        await send_file(selected_book, update, context)
    else:  # Send to Boox
        await update.message.reply_text("Sending to Boox...")
        await send_to_boox_handler(update, context, selected_book)
    await update.message.reply_text(
        "Done! You can start a new search anytime.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Search cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Create the conversation handler
book_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(["search", "s"], start_search),
        CommandHandler(["random", "r"], random_book_handler),
    ],
    states={
        SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_books)],
        SELECT_ACTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection)
        ],
        READY_TO_DELIVER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delivery)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
