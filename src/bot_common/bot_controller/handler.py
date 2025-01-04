import asyncio
import subprocess

from bot_common.bot_controller.bot_controller_config import BotControllerConfig
from bot_common.util import restricted
from telegram import Update
from telegram.ext import ContextTypes


@restricted
async def start_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    bot_name = update.message.text.split(" ")[1]
    bot_exec = bot_config.exec_script_map
    if bot_name not in bot_exec:
        await update.message.reply_text(f"{bot_name} not exists")
        return

    # with open(bot_log[bot_name], "w+") as logfile:
    p = subprocess.Popen(["bash", bot_exec[bot_name]], start_new_session=True)
    context.bot_data["exec_pid"].update({bot_name: p.pid})
    await asyncio.sleep(3)
    await update.message.reply_text(
        reply_to_message_id=update.message.message_id,
        text=f"BOT: {bot_name} \nPID: {p.pid}",
        parse_mode="HTML",
    )


@restricted
async def stop_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    bot_exec = bot_config.exec_script_map

    if (not update.message) or (not update.message.text):
        await update.message.reply_text("need bot name")
        return
    msg = update.message.text.split(" ")
    if len(msg) <= 1:
        await update.message.reply_text("need bot name")
        return
    bot_name = msg[1]
    if bot_name not in bot_exec:
        await update.message.reply_text(f"{bot_name} not exists")

    pid = context.bot_data["exec_pid"].get(bot_name, None)
    if pid:
        subprocess.run(["pkill", "-s", str(pid)])
        context.bot_data["exec_pid"].update({bot_name: None})
        await update.message.reply_text(
            text=f"{bot_name}: {pid} stopped",
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id,
        )
    else:
        await update.message.reply_text(
            text=f"{bot_name} is NOT running",
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id,
        )


@restricted
async def stop_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    bot_exec = bot_config.exec_script_map
    messages = []
    for bot_name, _ in bot_exec.items():
        pid = context.bot_data["exec_pid"].get(bot_name, None)
        if pid:
            subprocess.run(["pkill", "-s", str(pid)])
            context.bot_data["exec_pid"].update({bot_name: None})
            messages.append(f"{bot_name}: {pid} stopped")
    if not messages:
        messages = ["no running bots"]
    await update.message.reply_text(
        text="\n".join(messages),
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )


@restricted
async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.split(" ")
    p = subprocess.run(msg[1:], start_new_session=True, stdout=subprocess.PIPE)
    await asyncio.sleep(3)
    await update.message.reply_text(
        text=f"test run, {p.stdout.decode('utf-8')}", parse_mode="HTML"
    )


@restricted
async def list_active_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    messages = [
        f"{bot_name}: {pid}"
        for bot_name, pid in context.bot_data["exec_pid"].items()
        if pid
    ]
    if not messages:
        messages = ["no running bots"]
    await update.message.reply_text(
        text="\n".join(messages),
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )


@restricted
async def list_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    messages = sorted(bot_config.exec_script_map.keys())
    await update.message.reply_text(
        text="\n".join(messages),
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )


@restricted
async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_all_handler(update, context)
    exit(0)


@restricted
async def restart_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop_all_handler(update, context)
    bot_config: BotControllerConfig = context.bot_data["bot_config"]
    bot_exec = bot_config.exec_script_map
    for bot_name, _ in bot_exec.items():
        p = subprocess.Popen(["bash", bot_exec[bot_name]], start_new_session=True)
        context.bot_data["exec_pid"].update({bot_name: p.pid})
        await asyncio.sleep(3)
    await update.message.reply_text(
        text="\n".join("done"),
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id,
    )
