import logging
import tempfile

import aiohttp
from neodb.item import NeoDBItem
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from neodb.neodb import Visibility

# Define conversation states
SEARCH, SELECT_ITEM, CHOOSE_ACTION, ACTION_INPUT = range(4)


async def download_image(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        if response.status == 200:
            f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            f.write(await response.read())
            f.close()
            return f.name
    return ""


async def  compose_reply_message(item: NeoDBItem) -> InputMediaPhoto:
    async with aiohttp.ClientSession() as session:
        # Download the cover image
        image_path = await download_image(session, item.cover_image_url)

        # Compose the HTML message
        caption = f"<b>{item.category}</b>\n"
        caption += f"<b>Title:</b> {item.title}\n"
        caption += f"<b>By:</b> {item.by}\n"
        caption += f"<a href='{item.url}'>{item.url}</a>\n"
        if item.category == "book":
            caption += f"<b>ISBN:</b> {item.isbn}\n"
        # caption += f"<b>Description:</b> {item.description[:280]}\n"
        # Create InputMediaPhoto object
        media = InputMediaPhoto(
            media=open(image_path, "rb"), caption=caption, parse_mode="HTML"
        )
        return media


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter your search query:")
    return SEARCH


async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_state"] = SEARCH
    query = update.message.text.lower()
    bot_config = context.bot_data["bot_config"]
    search_results = bot_config.neodb_object.search_items(query, 1)
    logging.getLogger(__name__).info(f"search_results: {len(search_results)}")

    status, results = search_results
    results = results[: (bot_config.max_item_per_query)]
    if status != 200 or not results:
        await update.message.reply_text("No items found. Please try again.")
        return SEARCH

    keyboard = [
        [
            InlineKeyboardButton(
                item.category + "_" + item.title, callback_data=item.uuid
            )
        ]
        for item in results
    ] + [[InlineKeyboardButton("EXIT", callback_data="exit")]]

    context.user_data["search_results"] = {result.uuid: result for result in results}

    for item in results:
        item_media_message = await compose_reply_message(item)
        await update.message.reply_media_group([item_media_message])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please Select an item:", reply_markup=reply_markup)
    return SELECT_ITEM


async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_state"] = SELECT_ITEM
    query = update.callback_query
    await query.answer()
    if query.data == "exit":
        return ConversationHandler.END
    item_uuid = query.data
    context.user_data["selected_item"] = context.user_data["search_results"][item_uuid]

    keyboard = [
        [InlineKeyboardButton("Complete-OnlyMe", callback_data="complete-onlyme")],
        [
            InlineKeyboardButton(
                f"{rating}", callback_data=f"complete-onlyme-rating-{rating}"
            )
            for rating in range(1, 6)
        ],
        [InlineKeyboardButton("Complete-Public", callback_data="complete-public")],
        [
            InlineKeyboardButton(
                f"{rating}", callback_data=f"complete-public-rating-{rating}"
            )
            for rating in range(1, 6)
        ],
        [InlineKeyboardButton("Wish-OnlyMe", callback_data="wish-onlyme")],
        [InlineKeyboardButton("Wish-Public", callback_data="wish-public")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Selected: {context.user_data['selected_item'].title}\nChoose an action:",
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

    if action.startswith("complete") or action.startswith("wish"):
        await query.edit_message_text(
            f"You've chosen to {action} on {context.user_data['selected_item'].title}. "
            "Please enter any additional text or skip:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("SKIP", callback_data="skip")
                    ]
                ]
            ),
        )
        return ACTION_INPUT
    else:
        # Handle other actions that don't require text input
        return ConversationHandler.END


async def perform_action_with_input_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["current_state"] = ACTION_INPUT
    if update.callback_query:
        await update.callback_query.answer()
        comment_text_after_action = ""
    else:
        comment_text_after_action = update.message.text

    item_action = context.user_data.get("action")
    item: NeoDBItem = context.user_data["selected_item"]

    action_breakdown = item_action.split("-")
    if action_breakdown[0] == "complete":
        status, response = context.bot_data["bot_config"].neodb_object.mark_complete(
            item.uuid,
            comment_text_after_action,
            Visibility.SELF if action_breakdown[1] == "onlyme" else Visibility.PUBLIC,
            int(action_breakdown[3]) if len(action_breakdown) > 2 else None,
        )
        if status == 200:
            await context.bot.send_message(
                update.effective_user.id,
                f"Marked as completed with note: {comment_text_after_action}",
            )
        else:
            await context.bot.send_message(
                update.effective_user.id,
                f"Failed to mark as completed: {status}, {response}",
            )
    elif action_breakdown[0] == "wish":
        logging.getLogger(__name__).info(f"marking wish for {item.uuid}")
        status, response = context.bot_data["bot_config"].neodb_object.mark_wish(
            item.uuid,
            comment_text_after_action,
            Visibility.SELF if action_breakdown[1] == "onlyme" else Visibility.PUBLIC,
        )
        if status == 200:
            await context.bot.send_message(
                update.effective_user.id,
                f"Marked as wish to read with note: {comment_text_after_action}",
            )
        else:
            await context.bot.send_message(
                update.effective_user.id,
                f"Failed to mark as wish to read: {status}, {response}",
            )
    else:
        await context.bot.send_message(
            update.effective_user.id,
            f"action {item_action} not implemented in this example",
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
                    filters.TEXT & ~filters.COMMAND, perform_action_with_input_text
                ),
                CallbackQueryHandler(perform_action_with_input_text),
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
