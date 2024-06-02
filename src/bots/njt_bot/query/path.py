from dataclasses import dataclass
from enum import Enum

import pandas as pd
import requests


class PathStation(Enum):
    EXCHANGE_PLACE = "exchange_place", "Exchange Pl", "ep"
    CHRIST = "christopher_street", "Christopher St", "chris"
    GROVE = "grove_street", "Grove St", "grove"
    HARRISON = "harrison", "Harrison", "harrison"
    HOBOKEN = "hoboken", "Hoboken", "hoboken"
    JSQ = "journal_square", "Journal Sq", "jsq"
    NEWARK = "newark", "Newark", "newark"
    NEWPORT = "newport", "Newport", "newport"
    ST9 = "ninth_street", "9th St", "9"
    ST14 = "fourteenth_street", "14th St", "14"
    ST23 = "twenty_third_street", "23rd St", "23"
    ST33 = "thirty_third_street", "33rd St", "33"
    WTC = "world_trade_center", "World Trade Center", "wtc"

    def __init__(self, api_name: str, display_name: str, tg_command: str):
        self.api_name = api_name
        self.display_name = display_name
        self.tg_command = tg_command

    @staticmethod
    def get_station_map():
        return {x.tg_command: x for x in PathStation}


class PathLine(Enum):
    WTC = "WTC", PathStation.NEWARK, PathStation.WTC
    ST33 = "ST33", PathStation.JSQ, PathStation.ST33
    ST33_HOBOKEN = "ST33_HOBOKEN", PathStation.JSQ, PathStation.ST33
    HOBOKEN = "HOBOKEN", PathStation.HOBOKEN, PathStation.ST33

    def __init__(self, linename: str, nj_terminal: PathStation, ny_terminal: PathStation):
        self.linename = linename
        self.nj_terminal = nj_terminal
        self.ny_terminal = ny_terminal

    @staticmethod
    def string_map(api_name):
        return {
            "World Trade Center": PathLine.WTC,
            "33rd Street via Hoboken": PathLine.ST33_HOBOKEN,
            "Journal Square via Hoboken": PathLine.ST33_HOBOKEN,
            "Newark": PathLine.WTC,
            "33rd Street": PathLine.ST33,
            "Journal Square": PathLine.ST33,
            "Hoboken": PathLine.HOBOKEN,
        }[api_name]


@dataclass
class TrainStatus:
    line: PathLine
    direction: str
    arrival_time: pd.Timestamp


def get_train_status(path_station: PathStation):
    return requests.get(fr"https://path.api.razza.dev/v1/stations/{path_station.api_name}/realtime").json()


def html_format_path_status_output(current_station: PathStation, status_json: dict) -> str:
    train_status = [
        TrainStatus(
            PathLine.string_map(v["lineName"]),
            v["direction"],
            pd.Timestamp(v["projectedArrival"]).tz_convert("America/New_York"),
        )
        for v in status_json["upcomingTrains"]
    ]
    to_nj = [train for train in train_status if train.direction == "TO_NJ"]
    to_ny = [train for train in train_status if train.direction == "TO_NY"]

    html_str = f"<b>Station {current_station.display_name}</b>\n"
    html_str += "Next Train To New Jersey:\n" + "\n".join(
        [
            f"[Destination={train.line.nj_terminal.display_name}: "
            f"<b>{int((train.arrival_time - pd.Timestamp.utcnow().tz_convert('America/New_York')) / pd.Timedelta('1 min'))}</b> "
            f"min @ {train.arrival_time.strftime('%H:%M')}"
            for train in to_nj
        ]
    )

    html_str += "\n\nNext Train To New York:\n" + "\n".join(
        [
            f"[Destination={train.line.ny_terminal.display_name}: "
            f"<b>{int((train.arrival_time - pd.Timestamp.utcnow().tz_convert('America/New_York')) / pd.Timedelta('1 min'))} </b>"
            f"min @ {train.arrival_time.strftime('%H:%M')}"
            for train in to_ny
        ]
    )
    return html_str
