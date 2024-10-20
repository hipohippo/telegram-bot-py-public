from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import logging

# Define conversation states
SEARCH, SELECT_ITEM, CHOOSE_ACTION, ACTION_INPUT = range(4)


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter your search query:")
    return SEARCH


def format_search_results(
    results: dict, subkeys: dict, max_item_per_query: int
) -> dict:
    return {
        results["data"][i]["uuid"]: {
            k: str(results["data"][i].get(k, ""))
            for k in subkeys[results["data"][i]["category"]]
        }
        for i in range(min(max_item_per_query, len(results["data"])))
    }


async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ## TODO: add picture description
    
    context.user_data["current_state"] = SEARCH
    query = update.message.text.lower()
    search_results = context.bot_data["bot_config"].neodb_object.search_items(query, 1)
    logging.getLogger(__name__).info(f"search_results: {search_results}")

    status, results = search_results
    if status != 200 or not results:
        await update.message.reply_text("No items found. Please try again.")
        return SEARCH
    else:
        sliced_result = format_search_results(
            results,
            context.bot_data["bot_config"].subkeys,
            context.bot_data["bot_config"].max_item_per_query,
        )

    keyboard = [
        [
            InlineKeyboardButton(
                item["title"] + item.get("author", "_"), callback_data=uuid
            )
        ]
        for uuid, item in sliced_result.items()
    ]

    context.user_data["search_results"] = sliced_result
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Select an item:", reply_markup=reply_markup)
    return SELECT_ITEM


async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_state"] = SELECT_ITEM
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


async def handle_action_choice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["current_state"] = CHOOSE_ACTION
    query = update.callback_query
    await query.answer()

    action = query.data
    context.user_data["action"] = action

    if action in ["complete", "wish"]:
        await query.edit_message_text(
            f"You've chosen to {action} on {context.user_data['selected_item']['title']}. "
            "Please enter any additional text:"
        )
        return ACTION_INPUT
    else:
        # Handle other actions that don't require text input
        return ConversationHandler.END


async def perform_action_with_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["current_state"] = ACTION_INPUT
    action_text = update.message.text
    action = context.user_data.get("action")

    item: dict = context.user_data["selected_item"]

    if action == "complete":
        status, response = context.bot_data["bot_config"].neodb_object.mark_complete(
            item["uuid"], action_text
        )
        if status == 200:
            await update.message.reply_text(
                f"Marked as completed with note: {action_text}"
            )
        else:
            await update.message.reply_text(
                f"Failed to mark as completed: {status}, {response}"
            )
    elif action == "wish":
        logging.getLogger(__name__).info(f"marking wish for {item['uuid']}")
        status, response = context.bot_data["bot_config"].neodb_object.mark_wish(
            item["uuid"], action_text
        )
        if status == 200:
            await update.message.reply_text(
                f"Marked as wish to read with note: {action_text}"
            )
        else:
            await update.message.reply_text(
                f"Failed to mark as wish to read: {status}, {response}"
            )
    else:
        await update.message.reply_text(
            f"action {action} not implemented in this example"
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_state"] = ConversationHandler.END
    await update.message.reply_text("Search cancelled.")
    return ConversationHandler.END


async def show_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler to show the current state of the conversation."""
    user_id = update.effective_user.id

    # Check the current state
    current_state = context.user_data.get("current_state")

    # Map state integers to readable names
    state_names = {
        SEARCH: "Searched for items",
        SELECT_ITEM: "Selected an item",
        CHOOSE_ACTION: "Chose an action",
        ACTION_INPUT: "Received action details",
        ConversationHandler.WAITING: "Waiting for next command",
        ConversationHandler.END: "Conversation ended",
    }

    state_description = state_names.get(current_state, str(current_state))

    # Get additional context if available
    selected_item = context.user_data.get("selected_item", "No item selected")
    last_action = context.user_data.get("action", "No action chosen")

    message = f"User ID: {user_id}\n"
    message += f"Current state: {state_description}\n"
    message += f"Selected item: {selected_item}\n"
    message += f"Last action: {last_action}"

    await update.message.reply_text(message)


def get_conversation_handler() -> ConversationHandler:
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", start_search)],
        states={
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_items)],
            SELECT_ITEM: [CallbackQueryHandler(select_item)],
            CHOOSE_ACTION: [CallbackQueryHandler(handle_action_choice)],
            ACTION_INPUT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, perform_action_with_text
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("state", show_state),  # Add this line to show state
        ],
        name="neodb_conv",
        ## per_message=True, ## not sure if this is needed
    )
    return conv_handler
