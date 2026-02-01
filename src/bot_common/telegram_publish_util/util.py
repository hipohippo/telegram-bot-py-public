import logging
from typing import List

import numpy as np
from telegram import Update
from telegram.ext import ContextTypes

from bot_common.common_handler import heart_beat_job


async def send_message_with_retry(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, html_text: str
):
    i = 1
    MAX_ATTEMPTS = 2
    while i <= MAX_ATTEMPTS:
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=html_text, parse_mode="HTML"
            )
            return
        except Exception:
            await heart_beat_job(context)
            i += 1


async def channel_post_job(context: ContextTypes.DEFAULT_TYPE):
    target_chat_id = context.job.data["publish_channel_id"]
    telegraph_urls = context.job.data["telegraph_urls"]
    title = context.job.data["title"]
    original_url = context.job.data["original_url"]
    await channel_post_function(
        context, target_chat_id, telegraph_urls, original_url, title
    )


async def post_scraped_urls_to_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegraph_urls: List[str],
    original_url: str,
    title: str,
    error_notify_chat: int,
    publish_channel_id: int | str,
    delay_publish_max_minute: int,
):
    # reply orignal message with URL
    await update.message.reply_html("\n".join(telegraph_urls))

    # compose html message and publish to designated channel
    if update.message.chat_id != error_notify_chat and publish_channel_id:
        await schedule_delay_post_channel_job(
            context,
            telegraph_urls,
            original_url,
            title,
            publish_channel_id,
            delay_publish_max_minute,
        )


async def schedule_delay_post_channel_job(
    context: ContextTypes.DEFAULT_TYPE,
    telegraph_urls: List[str],
    original_url: str,
    title: str,
    publish_channel_id: int | str,
    delay_publish_max_minute: int,
):
    delay_minutes = int(np.random.uniform(0, delay_publish_max_minute, 1)[0])
    logging.info(f"delayed by {delay_minutes}/{delay_publish_max_minute}")
    context.application.job_queue.run_once(
        channel_post_job,
        data={
            "telegraph_urls": telegraph_urls,
            "original_url": original_url,
            "title": title,
            "publish_channel_id": publish_channel_id,
        },
        when=delay_minutes * 60,
        job_kwargs={"misfire_grace_time": 5},  ## per APScheduler
    )
    logging.getLogger(__name__).info(
        f"Publishing of {telegraph_urls} is scheduled to run after {delay_minutes} minutes"
    )


async def channel_post_function(
    context: ContextTypes.DEFAULT_TYPE,
    target_chat_id: int | str,
    telegraph_urls: List[str],
    original_url: str,
    title: str,
):
    for idx, telegraph_url in enumerate(telegraph_urls):
        numbering = (
            f"({(idx + 1)}/{len(telegraph_urls)})" if (len(telegraph_urls)) >= 2 else ""
        )
        message_for_channel = f'<a href="{telegraph_url}"> {title + numbering} </a> | <a href="{original_url}">原文</a>'
        await send_message_with_retry(
            context, chat_id=target_chat_id, html_text=message_for_channel
        )
        logging.getLogger(__name__).info(f"Publishing of {telegraph_url} is completed")
