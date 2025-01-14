import asyncio
import logging
import traceback

import pandas as pd
from bot_common.util import parse_channel_message_link
from telegram import BotCommand, Update
from telegram.ext import CallbackContext


async def init_command_menu(context: CallbackContext) -> None:
    commands = [
        BotCommand("reload", "Reload the suspicious keywords from the file"),
        BotCommand("add", "Add new suspicious keywords"),
        BotCommand("current", "Display current suspicious keywords"),
        BotCommand("delete", "Delete a post from a channel"),
        BotCommand("ban", "Ban a user from a channel"),
    ]
    await context.bot.set_my_commands(commands)


async def reply_current_keywords(update: Update, context: CallbackContext) -> None:
    bot_config = context.bot_data["bot_config"]
    suspicious_keywords = bot_config.suspicious_keywords
    if not suspicious_keywords:
        await update.message.reply_text("There are no suspicious keywords currently.")
    else:
        await update.message.reply_text(f"{', '.join(suspicious_keywords)}")


async def add_suspicious_keyword(update: Update, context: CallbackContext) -> None:
    bot_config = context.bot_data["bot_config"]
    new_keywords = context.args

    if not new_keywords:
        await update.message.reply_text("Please provide at least one keyword to add.")
        return

    added_keywords = []
    for new_keyword in new_keywords:
        new_keyword = new_keyword.strip()
        if new_keyword and new_keyword not in bot_config.suspicious_keywords:
            bot_config.suspicious_keywords.append(new_keyword)
            added_keywords.append(new_keyword)

    if not added_keywords:
        await update.message.reply_text(
            "All provided keywords are already in the list."
        )
        return

    try:
        with open(bot_config.suspicious_keywords_file, "a") as file:
            for keyword in added_keywords:
                file.write(f"{keyword}\n")
        await update.message.reply_text(
            f"Keywords '{', '.join(added_keywords)}' added successfully."
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to add keywords: {e}")


async def reload_suspicious_keywords(update: Update, context: CallbackContext) -> None:
    bot_config = context.bot_data["bot_config"]
    try:
        bot_config.suspicious_keywords = bot_config._parse_suspicious_keywords(
            bot_config.suspicious_keywords_file
        )
        await update.message.reply_text("Suspicious keywords reloaded successfully.")
    except Exception as e:
        await update.message.reply_text(f"Failed to reload suspicious keywords: {e}")


async def filter_handler(update: Update, context: CallbackContext) -> None:
    """Filter messages from managed channels and delete them if they contain suspicious keywords.
    1. We can fetch user id and group id from message directly. But we have to get channel id from reply_to_message.
    2. When we ban user, it has to be the group chat id, not the channel id.
    3. We have to save message id to user id mapping to a csv file.
    Args:
        update (Update): _description_
        context (CallbackContext): _description_
    """
    bot_config = context.bot_data["bot_config"]
    message = update.message
    reply_to_message = message.reply_to_message

    if not message or not reply_to_message:
        return

    content = ""

    if message.text:
        content += message.text
    if message.caption:
        content += message.caption

    user_id = message.from_user.id

    is_from_managed_channel = (
        message
        and reply_to_message.sender_chat
        and (reply_to_message.sender_chat.id in bot_config.managed_channels)
    )

    if not is_from_managed_channel:
        logging.getLogger(__name__).info(
            f"not from managed channel, channel_id: {reply_to_message.sender_chat.id}, channel_group_id: {message.chat.id}"
        )
        return

    channel_id = reply_to_message.sender_chat.id
    logging.getLogger(__name__).info(
        f"from managed channel, channel_id: {channel_id}, channel_group_id: {message.chat.id}"
    )

    group_chat_id = message.chat.id
    bot_config.message_id_to_user_id = pd.concat(
        [
            bot_config.message_id_to_user_id,
            pd.DataFrame(
                {
                    "message_id": [int(message.message_id)],
                    "user_id": [int(user_id)],
                }
            ),
        ],
        ignore_index=True,
    ).reset_index(drop=True)

    logging.getLogger(__name__).info(
        f"Saved message ID {message.message_id} to user ID {user_id}."
    )

    if content and any(
        keyword.upper() in content.upper() for keyword in bot_config.suspicious_keywords
    ):
        try:
            logging.getLogger(__name__).info(f"Deleting message...{content}")
            await asyncio.sleep(1)
            await context.bot.delete_message(
                chat_id=group_chat_id, message_id=message.message_id
            )
            logging.getLogger(__name__).info(
                f"Deleted message from user {user_id} in channel group {group_chat_id}, channel {channel_id} containing suspicious {content}."
            )
            await ban_user_function(context, user_id, group_chat_id)
        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to delete message: {e} from group {group_chat_id}, channel {channel_id}, message_id: {message.message_id}, by {user_id}"
            )


async def delete_post_handler(update: Update, context: CallbackContext) -> None:
    bot_config = context.bot_data["bot_config"]
    link = context.args[0]

    channel_group_id, post_id, thread_id = parse_channel_message_link(link)

    # Delete the original comment
    try:
        group_id = bot_config.managed_channel_groups[1]
        await context.bot.delete_message(chat_id=group_id, message_id=post_id)
        logging.getLogger(__name__).info(
            f"Deleted message {post_id}, thread {thread_id}, from channel {group_id}."
        )
        user_id = bot_config.message_id_to_user_id[
            bot_config.message_id_to_user_id["message_id"] == int(post_id)
        ]["user_id"]
        if len(user_id) > 0:
            user_id = int(user_id.iloc[0])
        else:
            logging.getLogger(__name__).error(
                f"No user ID found for message {post_id} in channel {group_id}."
            )
            return
        await context.bot.ban_chat_member(
            chat_id=group_id, user_id=user_id, revoke_messages=True
        )
        logging.getLogger(__name__).info(
            f"Banned user {user_id} in channel {group_id}."
        )
    except Exception:
        logging.getLogger(__name__).error(
            f"Exception: {traceback.format_exc()}, channel_group_id: {group_id}, post_id: {post_id}, thread_id: {thread_id}"
        )


async def ban_user_function(
    context: CallbackContext, user_id: int, group_chat_id: int
) -> None:
    bot_config = context.bot_data["bot_config"]
    if user_id not in bot_config.do_not_ban_user_ids:
        await context.bot.ban_chat_member(chat_id=group_chat_id, user_id=user_id)
        logging.getLogger(__name__).info(
            f"Banned user {user_id} in channel group {group_chat_id}."
        )
    else:
        logging.getLogger(__name__).info(
            f"User {user_id} is in do not ban user list, skipping ban."
        )


async def ban_user_handler(update: Update, context: CallbackContext) -> None:
    userid = context.args[0]
    group_chat_id = context.bot_data["bot_config"].managed_channel_groups[1]
    await ban_user_function(context, userid, group_chat_id)


async def save_message_id_to_user_id(context: CallbackContext) -> None:
    """Periodically save message ID to user ID mapping to CSV file"""
    bot_config = context.bot_data["bot_config"]
    try:
        # Save the DataFrame to CSV
        bot_config.message_id_to_user_id.to_csv(
            bot_config.message_id_to_user_id_file, index=False
        )
        logging.getLogger(__name__).info(
            f"Successfully saved message ID to user ID mapping to {bot_config.message_id_to_user_id_file}"
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to save message ID to user ID mapping: {e}"
        )
