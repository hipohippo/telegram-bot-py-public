import logging
from typing import List, Tuple, Optional

from telegram.ext import BaseHandler, Application, ApplicationBuilder, Defaults, CommandHandler
from telegram.ext._utils.types import JobCallback, CCT

from bot_common.bot_config.bot_config import BotConfig
from bot_common.common_handler import poke_handler, heart_beat_job


## not in use. to be deprecated
def bot_factory(
    bot_token: str,
    bot_config: BotConfig,
    handlers: Optional[List[BaseHandler]],
    repeating_jobs: Optional[List[Tuple[JobCallback[CCT], dict]]],
    onetime_jobs: Optional[List[Tuple[JobCallback[CCT], dict]]],
) -> Application:
    application = (
        ApplicationBuilder()
        .token(bot_token)
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .concurrent_updates(3)
        .build()
    )
    application.bot_data["bot_config"] = bot_config
    if handlers:
        application.add_handlers(handlers)

    if repeating_jobs:
        for repeating_job in repeating_jobs:
            application.job_queue.run_repeating(repeating_job[0], **repeating_job[1])

    if onetime_jobs:
        for onetime_job in onetime_jobs:
            application.job_queue.run_once(onetime_job[0], **onetime_job[1])
    return application


class BotBuilder:
    default_repeating_jobs = [(heart_beat_job, {"first": 5, "interval": 4 * 60 * 60})]
    default_handler = [
        CommandHandler("poke", poke_handler),
    ]

    def __init__(self, bot_token: str, bot_config: BotConfig):
        self.bot_token = bot_token
        self.bot_config = bot_config
        self.handlers = self.default_handler.copy()
        self.repeating_jobs = self.default_repeating_jobs.copy()
        self.daily_jobs = []
        self.error_handler = None
        self.onetime_jobs = []

    def add_handlers(self, handlers: List[BaseHandler]):
        self.handlers.extend(handlers)
        return self

    def add_error_handler(self, error_handler: BaseHandler):
        self.error_handler = error_handler

    def add_onetime_jobs(self, onetime_jobs: List[Tuple[JobCallback[CCT], dict]]):
        self.onetime_jobs.extend(onetime_jobs)
        return self

    def add_repeating_jobs(self, repeating_jobs: List[Tuple[JobCallback[CCT], dict]]):
        self.repeating_jobs.extend(repeating_jobs)
        return self

    def add_daily_job(self, daily_jobs: List[Tuple[JobCallback[CCT], dict]]):
        self.daily_jobs.extend(daily_jobs)
        return self

    def build(self):
        # do not await handler
        # https://stackoverflow.com/questions/77034884/how-to-make-my-telegram-bots-handler-not-block-each-other
        df = Defaults(block=False)
        logging.getLogger("httpx").setLevel("WARNING")
        application = (
            ApplicationBuilder()
            .token(self.bot_token)
            .http_version("1.1")
            .get_updates_http_version("1.1")
            .concurrent_updates(3)
            .defaults(df)  #
            .build()
        )
        application.bot_data["bot_config"] = self.bot_config
        application.add_handlers(self.handlers)
        if self.error_handler:
            application.add_error_handler(self.error_handler)

        for repeating_job in self.repeating_jobs:
            application.job_queue.run_repeating(repeating_job[0], **repeating_job[1])

        for onetime_job in self.onetime_jobs:
            application.job_queue.run_once(onetime_job[0], **onetime_job[1])

        for daily_job in self.daily_jobs:
            application.job_queue.run_daily(daily_job[0], **daily_job[1])
        return application
