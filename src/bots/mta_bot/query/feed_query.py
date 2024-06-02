from enum import Enum
from typing import List, Tuple

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict

from bots.mta_bot.query.util import get_ny_time


class RouteGroup(Enum):
    ACE = "-ace"
    BDFM = "-bdfm"
    NQRW = "-nqrw"
    G = "-g"
    JZ = "-jz"
    L = "-l"
    NUMBER = ""


route_stop_group = {"ACE", "BDFM", "NQRW", "GHJLSZ", "123", "456", "7"}
route_stop_map = dict()
[route_stop_map.update({route: route_group for route in route_group}) for route_group in route_stop_group]


def query_stop_and_route(
    stop_parent_id: str, direction: str, route: RouteGroup, api_key: str
) -> List[Tuple[str, pd.Timestamp]]:
    train_feed = _query_feed(route, api_key)
    station_time = _parse_stop_time(train_feed, f"{stop_parent_id}{direction}")
    return station_time


def query_all_stations_for_route(route: str, stop_info_df: pd.DataFrame) -> pd.DataFrame:
    route_stop_group = list(route_stop_map.get(route, []))
    stops = stop_info_df[stop_info_df["route"].isin(route_stop_group)][["stop_name", "stop_id"]]
    return stops


def _query_feed(route: RouteGroup, api_key: str) -> dict:
    resp = requests.get(
        f"https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs{route.value}",
        headers={"x-api-key": api_key, "key": api_key,},
        # params={"hour": "10", "minute": "25"},
    )
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    train_feed = protobuf_to_dict(feed)["entity"]
    return train_feed


def _parse_stop_time(train_feed: dict, stop_id: str) -> List[Tuple[str, pd.Timestamp]]:
    train_at_station = []
    for train in train_feed:  # trains are dictionaries
        train_schedule = train.get("trip_update", {})  # train_schedule is a dictionary with trip and stop_time_update
        train_route = train_schedule.get("trip", {}).get("route_id", None)
        # train_direction = train_schedule.get("trip", {}).get("direction", None)
        if train_route is None:
            continue
        arrivals = train_schedule.get("stop_time_update", [])  # arrival_times is a list of arrivals
        for scheduled_arrival in arrivals:  # arrivals are dictionaries with time data and stop_ids
            if scheduled_arrival.get("stop_id", None) == stop_id:
                arrival_time = scheduled_arrival.get("arrival", {}).get("time", None)
                if arrival_time and arrival_time > int(pd.Timestamp.now().timestamp()):
                    arrival_time = get_ny_time(arrival_time)
                    train_at_station.append((train_route, arrival_time))
    train_at_station.sort(key=lambda element: element[1])
    return train_at_station
