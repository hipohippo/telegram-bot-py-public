import re
from enum import Enum
from typing import List

import pandas as pd


class NJTBusStop(Enum):
    def __init__(self, stop_name: str, direction: str, id: int):
        self.stop_name: str = stop_name
        self.direction: str = direction
        self.id: int = id

    def __str__(self):
        return f"{self.name}, {self.id}"

    LHNY = "LH", "NY", 21831  ## lincoln harbor toward new york
    LHNJ = "LH", "NJ", 21830  ## lincoln harbor toward new jersey
    PABT = "PABT", "NJ", 21830  ## port authority bus terminal toward new jersey
    RWNY = "RW", "NY", 21923


class NextBus:
    def __init__(self, bus_number: str, predicted_departure_str: str, vehicle_info: str):
        """
        :param stop:
        :param predicted_time:  must match the regex {[\d]+ MIN"
        :param bus_number:      <rn>
        """
        self.bus_number = bus_number
        self.predicted_departure_min: int = re.match(r"[^\d]*([\d]+)[ ]*MIN", predicted_departure_str)[1]
        self.departure_time = pd.Timestamp.now() + pd.Timedelta(f"{self.predicted_departure_min} min")
        self.vehicle_info = vehicle_info

    def to_html(self) -> str:
        return (
            f"{self.bus_number}: <b>{self.predicted_departure_min} MIN</b> @ <b>{self.departure_time.strftime('%I:%M %p')} "
            f"{self.vehicle_info}</b>"
        )


def format_bus_message(stop: NJTBusStop, bus_arrivals: List[NextBus], direction: str) -> str:
    message = (f"To <b>{direction}</b> StopID={stop.id}:\n") + (
        "\n".join([bus.to_html() for bus in bus_arrivals if bus.departure_time >= pd.Timestamp.now()])
        if bus_arrivals
        else "No bus found"
    )
    return message
