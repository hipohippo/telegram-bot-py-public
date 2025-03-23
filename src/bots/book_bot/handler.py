from pathlib import Path
from typing import List

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
from bots.book_bot.book_db import search_book_df

# Define states
SEARCH, SELECT_ACTION, READY_TO_DELIVER = range(3)


@restricted
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text("Please enter keywords to search for a book:")
    return SEARCH


@restricted
async def search_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Search for books based on keywords and show results."""
    keywords = update.message.text
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
                [["Send to chat", "Send to LAN"]], one_time_keyboard=True
            ),
        )
        return READY_TO_DELIVER

    except ValueError:
        await update.message.reply_text("Please enter a valid number")
        return SELECT_ACTION


@restricted
async def handle_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the delivery method for the selected book."""
    choice = update.message.text
    selected_book: Path = context.user_data["selected_book"]

    if choice not in ["Send to chat", "Send to LAN"]:
        await update.message.reply_text(
            "Please select a valid option.",
            reply_markup=ReplyKeyboardMarkup(
                [["Send to chat", "Send to LAN"]], one_time_keyboard=True
            ),
        )
        return READY_TO_DELIVER

    if choice == "Send to chat":
        # Send the file directly in chat
        await send_file(selected_book, update, context)
    else:  # Send to LAN
        # Use subprocess to send to local network. TODO: Fix this
        await update.message.reply_text("Sending to LAN...")
        # await send_file(selected_book, update, context)
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
    entry_points=[CommandHandler("search", start_search)],
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
