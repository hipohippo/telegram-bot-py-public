from telegram import Update, BotCommand
from telegram.ext import ContextTypes

from bot_common.util import restricted
from bots.njt_bot.query.bus_and_stop import NJTBusStop
from bots.njt_bot.query.bus_api import next_bus_job
from bots.njt_bot.query.lightrail_alert import get_hblr_alert
from bots.njt_bot.query.path import html_format_path_status_output, get_train_status, PathStation


async def init_cmd(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.setMyCommands(
        [BotCommand("/ny", "NYC Next Bus"), BotCommand("/nj", "NJ Next Bus"), BotCommand("/lr", "Light Rail Alert")]
    )


@restricted
async def next_bus_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (not update.message) or (not update.message.text):
        return
    direction = (update.message.text.split("/")[1]).upper()
    if direction not in {"NY", "NJ"}:
        await update.message.reply_text(text="unable to recognize direction")
        return
    stop = {"NY": NJTBusStop.RWNY, "NJ": NJTBusStop.LHNJ}[direction]
    next_bus_arrival = await next_bus_job(stop, direction, context.bot_data["browser"])
    await update.message.reply_text(text=next_bus_arrival, parse_mode="HTML")


async def lightrail_alert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lightrail_alert = get_hblr_alert()
    await update.message.reply_text(lightrail_alert, parse_mode="HTML")
    return lightrail_alert


async def path_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    station_query = update.message.text[1:]
    station_map = PathStation.get_station_map()
    if not station_query in station_map.keys():
        await update.message.reply_text(f"unknown station name. choose from f{' '.join(station_map.keys())}")
        return

    current_station = station_map.get(station_query)
    path_train_status = html_format_path_status_output(current_station, get_train_status(current_station))
    await update.message.reply_text(path_train_status, parse_mode="HTML")
