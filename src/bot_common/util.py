import logging
from configparser import SectionProxy
from functools import wraps
from typing import Callable, List, Optional

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
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if (context.bot_data["bot_config"].white_list_id is not None) and (
            user_id not in context.bot_data["bot_config"].white_list_id
        ):
            logging.getLogger(__name__).error(f"Unauthorized access denied for {user_id}")
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def format_white_list(white_list_str: Optional[str]) -> Optional[List[int]]:
    return [int(x.strip()) for x in white_list_str.split(",")] if white_list_str else None


def slice_list_for_keyboard_layout(x: list, size: int):
    """
    slice_list_for_keyboard_layout([1,2,3,4,5], 3) = [[1,2,3], [4,5]]
    :param x:
    :param size:
    :return: 2-dim list that every element has length equals to size
    """
    return [x[(size * j) : (size * j + size)] for j in range((len(x) - 1) // size + 1)]
