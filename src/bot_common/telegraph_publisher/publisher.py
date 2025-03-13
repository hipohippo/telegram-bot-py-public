import asyncio
import logging
import time
import traceback
from typing import List

import pandas as pd
from telegram import Update
from telegram.ext import ContextTypes
from telegraph import Telegraph


def publish_single(
    telegraph_publisher: Telegraph, title: str, author: str, html_content: str
) -> str:
    attempt = 1
    MAX_ATTEMPT = 2
    last_error = None
    while attempt <= MAX_ATTEMPT:
        try:
            response = telegraph_publisher.create_page(
                title=title,
                author_name=author,
                html_content=html_content,
            )
            url = response["url"]
            logging.getLogger(__name__).info(f"published to {url}")
            return url
        except Exception as e:
            if attempt == MAX_ATTEMPT:
                with open(
                    f"error_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w"
                ) as f:
                    f.write(html_content)
            last_error = e
            logging.getLogger(__name__).error(e)
            time.sleep(3)
            attempt += 1
    raise last_error


def chop_str_group(str_list: List[str], chunk_size: int) -> List[int]:
    """

    :param html_content_group:  a list of str
    :return: list of index i0, i1, i2 such that, each string between neighbor index satisfies that
             len("".join(str_list[i0:i1])) <= chunk_size
             i0 = 0 always
             presumably the length of each string in the list is less than the chunk_size
    """
    cutoff_index = [0]
    prev_len = 0
    for idx, cur_str in enumerate(str_list):
        if prev_len + len(cur_str) > chunk_size:
            cutoff_index.append(idx)
            prev_len = len(cur_str)
        else:
            prev_len += len(cur_str)
    cutoff_index.append(len(str_list))
    return cutoff_index


def publish_chunk_telegraph(
    telegraph_publisher: Telegraph,
    title: str,
    author: str,
    html_content_group: List[str],
) -> List[str]:
    cutoff_index = chop_str_group(html_content_group, chunk_size=20000)
    logging.getLogger(__name__).info(
        f"total html length {sum([len(s) for s in html_content_group])}, cutoff_index {cutoff_index}"
    )
    url_list = []
    for idx in range(len(cutoff_index) - 1):
        url_list.append(
            publish_single(
                telegraph_publisher,
                title + f" ({idx + 1}/{len(cutoff_index) - 1})"
                if (len(cutoff_index) >= 3)
                else title,
                author,
                "".join(html_content_group[cutoff_index[idx] : cutoff_index[idx + 1]]),
            )
        )
        if idx != len(cutoff_index) - 2:
            time.sleep(10)
    return url_list


async def publish_chunk_to_telegraph(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegraph_publisher: Telegraph,
    title: str,
    author: str,
    html_element_list: List[str],
    error_notify_chat: int,
):
    try:
        logging.getLogger(__name__).info(
            f"total html length {sum([len(s) for s in html_element_list])}"
        )
        telegraph_urls: List[str] = publish_chunk_telegraph(
            telegraph_publisher, title, author, html_element_list
        )
        return telegraph_urls
    except Exception:
        error_message = (
            f"failed in chat {update.effective_chat.id}: {traceback.format_exc()}"
        )
        logging.getLogger(__name__).error(error_message)
        await context.bot.send_message(error_notify_chat, text=error_message)
        await asyncio.sleep(5)
    return []
