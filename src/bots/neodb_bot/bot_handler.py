from telegram import Update
from telegram.ext import ContextTypes

import logging


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.split(" ")
    if len(query) <= 1:
        await update.message.reply_text("Please provide a search query.")
        return
    else:
        neodb_config = context.bot_data["bot_config"]
        neodb = neodb_config.neodb_object
        status, res = neodb.search_items(query, 1)
        if status == 200:
            sliced_res = [
                str(i)
                + "_"
                + ", ".join([str(res["data"][i].get(k, "")) for k in neodb_config.subkeys[res["data"][i]["category"]]])
                for i in range(min(neodb_config.max_item_per_query, len(res["data"])))
            ]
            joined_res = "\n".join(sliced_res)
            logging.getLogger(__name__).info(f"sliced_res: {joined_res}")
            await update.message.reply_text(joined_res)
        else:
            await update.message.reply_text(f"No results found or error occurred. {status}")
