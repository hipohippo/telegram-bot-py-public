from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import logging

# Define conversation states
SEARCH, SELECT_ITEM, CHOOSE_ACTION = range(3)


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter your search query:")
    return SEARCH


async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.message.text.lower()
    search_results = context.bot_data["bot_config"].neodb_object.search_items(query, 1)
    logging.getLogger(__name__).info(f"search_results: {search_results}")

    status, results = search_results
    if status != 200 or not results:
        await update.message.reply_text("No items found. Please try again.")
        return SEARCH
    else:
        sliced_result = {
            results["data"][i]["uuid"]: {
                k: str(results["data"][i].get(k, ""))
                for k in context.bot_data["bot_config"].subkeys[
                    results["data"][i]["category"]
                ]
            }
            for i in range(
                min(
                    context.bot_data["bot_config"].max_item_per_query,
                    len(results["data"]),
                )
            )
        }

    keyboard = [
        [InlineKeyboardButton(item["title"] + item.get("author",0), callback_data=uuid)]
        for uuid, item in sliced_result.items()
    ]

    context.user_data["search_results"] = sliced_result
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Select an item:", reply_markup=reply_markup)
    return SELECT_ITEM


async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    item_uuid = query.data
    context.user_data["selected_item"]: dict = context.user_data["search_results"][
        item_uuid
    ]

    keyboard = [
        [InlineKeyboardButton("Complete", callback_data="complete")],
        [InlineKeyboardButton("Wish", callback_data="wish")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Selected: {context.user_data['selected_item']['title']}\nChoose an action:",
        reply_markup=reply_markup,
    )
    return CHOOSE_ACTION


async def perform_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    action = query.data
    item: dict = context.user_data["selected_item"]

    if action == "complete":
        context.bot_data["bot_config"].neodb_object.mark_complete(
            item["uuid"], "complete"
        )
    elif action == "wish":
        logging.getLogger(__name__).info(f"marking wish for {item['uuid']}")
        status, response = context.bot_data["bot_config"].neodb_object.mark_wish(item["uuid"])
        await query.edit_message_text(f"Marking wish for {item['uuid']} status: {status}")
    else:
        await query.edit_message_text(
            f"Deleting {item['title']} (not implemented in this example)"
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Search cancelled.")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", start_search)],
        states={
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_items)],
            SELECT_ITEM: [CallbackQueryHandler(select_item)],
            CHOOSE_ACTION: [CallbackQueryHandler(perform_action)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
