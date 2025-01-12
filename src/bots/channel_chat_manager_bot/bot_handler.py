import asyncio

from telegram import BotCommand, Update
from telegram.ext import CallbackContext


async def init_command_menu(context: CallbackContext) -> None:
    commands = [
        BotCommand("reload_keywords", "Reload the suspicious keywords from the file"),
        BotCommand("add_keywords", "Add new suspicious keywords"),
        BotCommand("current_keywords", "Display the current suspicious keywords"),
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
    suspicious_users = set()
    message = update.message

    if message:
        content = message.text
        user_id = message.from_user.id
        chat_id = message.chat_id
        is_from_managed_channel = (
            message.reply_to_message
            and message.reply_to_message.sender_chat
            and (message.reply_to_message.sender_chat.id in bot_config.managed_channels)
        )
        # print(message)
        if (
            any(keyword in content.upper() for keyword in suspicious_keywords)
            and is_from_managed_channel
        ):
            try:
                print("Deleting message...")
                await asyncio.sleep(1)
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=message.message_id
                )
                suspicious_users.add(user_id)
                print(
                    f"Deleted message from user {user_id} in channel {chat_id} containing suspicious {content}."
                )
            except Exception as e:
                print(f"Failed to delete message: {e}")
