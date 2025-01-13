import logging
from configparser import SectionProxy
from functools import wraps
from typing import Callable, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext._utils.types import HandlerCallback


def section_proxy_to_dict(section_proxy: SectionProxy) -> dict:
    return {k: v for k, v in section_proxy.items()}


def update_irrelevant_callback_wrapper(f: Callable) -> HandlerCallback:
    """
    wrap a callable that does not use input from update or context.
    convert to standard callback
    :param f:
    :return:
    """

    async def standard_callable(update: Update, context):
        f()

    return standard_callable


def check_white_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return (
        update.effective_user
        and update.effective_user.id
        and update.effective_user.id in context.bot_data["bot_config"].white_list_id
    )


def restricted(func):
    """
    decorator to restrict access. No restriction if white_list_id is None
    note: wraps(func) keeps original docstring and name of the wrapped function
    :param func:
    :return:
    """

    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if (context.bot_data["bot_config"].white_list_id is not None) and (
            user_id not in context.bot_data["bot_config"].white_list_id
        ):
            logging.getLogger(__name__).error(
                f"Unauthorized access denied for {user_id}"
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


def restricted_to_private_chat(func):
    """
    decorator to restrict access to private chat
    """

    @wraps(func)
    async def wrapped(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if update.message.chat.type != "private":
            logging.getLogger(__name__).error("only allowed in private chat")
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


def format_white_list(white_list_str: Optional[str]) -> Optional[List[int]]:
    return (
        [int(x.strip()) for x in white_list_str.split(",")] if white_list_str else None
    )


def slice_list_for_keyboard_layout(x: list, size: int):
    """
    slice_list_for_keyboard_layout([1,2,3,4,5], 3) = [[1,2,3], [4,5]]
    :param x:
    :param size:
    :return: 2-dim list that every element has length equals to size
    """
    return [x[(size * j) : (size * j + size)] for j in range((len(x) - 1) // size + 1)]


def parse_command_and_argument(text_message) -> Tuple[str, List[str]]:
    assert text_message[0] == "/"
    cmd = text_message.split(" ")
    return cmd[0], cmd[1:]


def parse_tg_channel_chat_link(link: str) -> Tuple[str, int, int]:
    """Extract channel username, post ID, and comment ID from the link."""
    # Example link: https://t.me/some_channel/7617?comment=16624
    try:
        base, query = link.split("?")
        channel_username, post_id = base.replace("https://t.me/", "").split("/")
        comment_id = query.split("=")[1]
        return channel_username, int(post_id), int(comment_id)
    except ValueError:
        raise ValueError("Invalid link format")


def parse_channel_message_link(link: str) -> Tuple[int, int, int]:
    """
    Extract the channel/group ID, message ID, and thread ID from the given Telegram link.

    Args:
        link (str): The Telegram link (e.g., https://t.me/c/123/456?thread=789).

    Returns:
        tuple: A tuple containing (channel_id, message_id, thread_id) as integers, or None if parsing fails.
    """
    try:
        # Parse the URL
        parsed_url = urlparse(link)

        # Ensure it's a valid Telegram URL
        if parsed_url.netloc != "t.me":
            raise ValueError("Invalid Telegram link format.")

        # Extract the path components
        path_parts = parsed_url.path.split("/")
        if len(path_parts) < 3:
            raise ValueError("Incomplete path in the link.")

        # Extract the query parameters
        query_params = parse_qs(parsed_url.query)

        # Handle both link formats
        if path_parts[1] == "c":
            # Format: t.me/c/123/456?thread=789
            channel_id = int(path_parts[2])
            post_id = int(path_parts[3])
            thread_id = (
                int(query_params.get("thread", [None])[0])
                if "thread" in query_params
                else None
            )
        else:
            # Format: t.me/groupname/789?comment=456
            channel_id = None
            thread_id = int(path_parts[2])
            post_id = (
                int(query_params.get("comment", [None])[0])
                if "comment" in query_params
                else None
            )

        return channel_id, post_id, thread_id

    except Exception as e:
        print(f"Error extracting IDs: {e}")
        return None, None, None
