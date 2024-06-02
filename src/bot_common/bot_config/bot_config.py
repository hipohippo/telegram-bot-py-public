from abc import ABC
from typing import List, Optional, Union


class BotConfig(ABC):
    def __init__(
        self,
        heart_beat_chat: Union[int, str],
        error_notify_chat: Union[int, str],
        white_list_id: Optional[List[int]],
        bot_name: str,
    ):
        """

        :param heart_beat_chat:
        :param error_notify_chat:
        :param bot_name:
        :param white_list_id: None means unrestricted
        """
        self._heart_beat_chat: int = int(heart_beat_chat)
        self._error_notify_chat: int = int(error_notify_chat)
        self._white_list_id: List[int] = white_list_id
        self._bot_name: str = bot_name

    @property
    def error_notify_chat(self) -> int:
        return self._error_notify_chat

    @property
    def heart_beat_chat(self) -> int:
        return self._heart_beat_chat

    @property
    def bot_name(self) -> str:
        return self._bot_name

    @property
    def white_list_id(self) -> List[int]:
        return self._white_list_id
