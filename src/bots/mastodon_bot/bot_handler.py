import logging
import os
import tempfile
from pathlib import Path
from typing import List

from bot_common.util import restricted, restricted_to_private_chat
from telegram import Update
from telegram.ext import ContextTypes


@restricted
@restricted_to_private_chat
async def post_to_mastodon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle Telegram messages and post them to Mastodon.
    This function extracts text and images from the Telegram update and posts them to Mastodon.

    Note that if the message contains multiple photos and caption, it will be effectivly a couple of updates,
        the first update is posted as first photo with caption,
        the rest updates are just post of other photos
        they do have the same media_group_id
    """
    # Get Mastodon object from bot config
    mastodon = context.bot_data["config"].mastodon_object

    # Extract text from the message
    income_text = update.message.text or update.message.caption or ""
    outgoing_text = income_text + " (发自我的手机)"

    # Extract images from the message
    outgoing_photo: List[str] = []
    if update.message.photo:
        largest_photo = update.message.photo[-1]
        photo_file_path = (
            Path(tempfile.gettempdir()) / f"temp_{largest_photo.file_id}.jpg"
        )
        photo_file = await largest_photo.get_file()
        await photo_file.download_to_drive(photo_file_path)
        outgoing_photo.append(photo_file_path)

    try:
        if outgoing_photo:
            # Post with media
            medias = [
                mastodon.media_post(photo, mime_type="image/jpeg")
                for photo in outgoing_photo
            ]
            media_ids = [media["id"] for media in medias]
            response = mastodon.status_post(outgoing_text, media_ids=media_ids)
        else:
            # Post text only
            response = mastodon.status_post(outgoing_text)

        logging.info(f"Successfully posted to Mastodon: {response}")
        await update.message.reply_text(
            "Successfully posted to Mastodon!", parse_mode="HTML"
        )

    except Exception as e:
        logging.error(f"Error posting to Mastodon: {str(e)}")
        await update.message.reply_text(
            "Failed to post to Mastodon. Please try again later."
        )
    finally:
        # Clean up downloaded photos
        for photo in outgoing_photo:
            if os.path.exists(photo):
                os.remove(photo)
