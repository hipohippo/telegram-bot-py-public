import itertools

from telegram import Update
from telegram.ext import ContextTypes

from bots.mta_bot.mta_bot_config import MTASubwayBotConfig
from nyc_mta.query.feed_query import query_stop_and_route, RouteGroup, query_all_stations_for_route
from nyc_mta.query.format import format_html
from nyc_mta.query.util import filter_by_time


async def next_train_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    accepted query case in-sensitive
    r/R
    A16N/a16n
    A16D/a16d
    :param update:
    :param context:
    :return:
    """
    if (not update) or (not update.message) or (not update.message.text):
        return

    bot_config: MTASubwayBotConfig = context.bot_data["bot_config"]
    query_text = update.message.text.upper()
    if query_text != "R":
        stop_parent_id = query_text[:3]
        direction = query_text[-1]
        context.user_data["last query"] = (stop_parent_id, direction)
    else:
        if "last query" in context.user_data:
            stop_parent_id, direction = context.user_data["last query"]
        else:
            await update.message.reply_text("no previous query")
            return

    direction = {"N": "N", "U": "N", "S": "S", "D": "S"}[direction]
    stop_arrivals = sorted(
        list(
            itertools.chain(
                *[
                    query_stop_and_route(stop_parent_id, direction, route_group, bot_config.api_key)
                    for route_group in RouteGroup
                ]
            )
        ),
        key=lambda item: item[1],
    )
    stop_arrivals = filter_by_time(stop_arrivals, bot_config.minute_departure_cap)
    stop_name = bot_config.stop_id_name_map[stop_parent_id]
    await update.message.reply_text(text=format_html(stop_name, direction, stop_arrivals), parse_mode="HTML")


async def show_stop_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    accepted query:
    /stop A
    /stop 7
    SA
    S7
    :param update:
    :param context:
    :return:
    """
    bot_config: MTASubwayBotConfig = context.bot_data["bot_config"]

    if (not update) or (not update.message) or (not update.message.text):
        return
    splits = update.message.text.split(" ")
    if splits[0] == "/stop" and len(splits) >= 2:
        route = splits[1][:1].upper()
    else:
        route = update.message.text[1].upper()

    stops = query_all_stations_for_route(route, bot_config.stop_info_df)
    msg = "\n".join([f"{stop['stop_name']} = {stop['stop_id']}" for idx, stop in stops.iterrows()])
    if msg != "":
        await update.message.reply_text(msg, parse_mode="HTML")


async def search_stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    accepted query
    s 42
    s grand
    s columb
    :param update:
    :param context:
    :return:
    """
    bot_config: MTASubwayBotConfig = context.bot_data["bot_config"]
    if (not update) or (not update.message) or (not update.message.text):
        return
    keyword = update.message.text[2:].lower()
    stops = bot_config.stop_info_df[bot_config.stop_info_df["stop_name"].str.lower().str.find(keyword) >= 0][
        ["stop_name", "stop_id"]
    ]
    msg = "\n".join([f"{stop['stop_name']} = {stop['stop_id']}" for idx, stop in stops.iterrows()])
    if len(msg) > 0:
        await update.message.reply_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_text("no such station", parse_mode="HTML")
