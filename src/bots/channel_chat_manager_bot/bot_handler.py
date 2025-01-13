import asyncio
import logging

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
    bot_config = context.bot_data["bot_config"]
    suspicious_keywords = bot_config.suspicious_keywords
    message = update.message

    if message:
        content = message.text
        user_id = message.from_user.id  ## question is this the actual user id?

        is_from_managed_channel = (
            message.reply_to_message
            and message.reply_to_message.sender_chat
            and (message.reply_to_message.sender_chat.id in bot_config.managed_channels)
        )

        if is_from_managed_channel:
            chat_id = message.reply_to_message.sender_chat.id
            bot_config.message_id_to_user_id = pd.concat(
                [
                    bot_config.message_id_to_user_id,
                    pd.DataFrame(
                        {"message_id": [message.message_id], "user_id": [user_id]}
                    ),
                ],
                ignore_index=True,
            ).reset_index(drop=True)

            logging.getLogger(__name__).info(
                f"Saved message ID {message.message_id} to user ID {user_id}."
            )
            if content and any(
                keyword.upper() in content.upper() for keyword in suspicious_keywords
            ):
                try:
                    logging.getLogger(__name__).info("Deleting message...")
                    await asyncio.sleep(1)
                    await context.bot.delete_message(
                        chat_id=chat_id, message_id=message.message_id
                    )
                    logging.getLogger(__name__).info(
                        f"Deleted message from user {user_id} in channel {chat_id} containing suspicious {content}."
                    )
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                    logging.getLogger(__name__).info(
                        f"Banned user {user_id} in channel {chat_id}."
                    )
                except Exception as e:
                    logging.getLogger(__name__).error(f"Failed to delete message: {e}")


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
            bot_config.message_id_to_user_id["message_id"] == post_id
        ]["user_id"]
        if len(user_id) > 0:
            user_id = user_id.iloc[0]
        else:
            logging.getLogger(__name__).error(
                f"No user ID found for message {post_id} in channel {group_id}."
            )
            return
        await context.bot.ban_chat_member(chat_id=group_id, user_id=user_id)
        logging.getLogger(__name__).info(
            f"Banned user {user_id} in channel {group_id}."
        )
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to delete message: {e}, channel_group_id: {channel_group_id}, post_id: {post_id}, thread_id: {thread_id}"
        )


## not in use
async def ban_user_handler(update: Update, context: CallbackContext) -> None:
    bot_config = context.bot_data["bot_config"]
    userid = context.args[0]
    chat_id = bot_config.managed_channels[0]

    if userid:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=userid)
        logging.getLogger(__name__).info(f"Banned user {userid} in channel {chat_id}.")


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
