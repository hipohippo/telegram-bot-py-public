from telegram import BotCommand
from telegram.ext import ContextTypes


async def init_menu_commands(context: ContextTypes.DEFAULT_TYPE):
    """
    pre-set commands in menu
    :param context:
    :return:
    """
    commands = [
        BotCommand("", ""),
    ]
    await context.bot.setMyCommands(commands)
