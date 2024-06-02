from typing import List, Tuple

import pandas as pd
import pytz


def get_ny_time(epoch_time: int):
    return (
        pd.Timestamp(pd.to_datetime(epoch_time, unit="s"), tzinfo=pytz.UTC)
        .tz_convert(pytz.timezone("America/New_York"))
        .tz_localize(None)
    )


def filter_by_time(stop_arrivals: List[Tuple[str, pd.Timestamp]], minute_departure_cap: int):
    return [
        (route, tm)
        for route, tm in stop_arrivals
        if pd.Timestamp.now() - pd.Timedelta(1, "min")
        <= tm
        <= pd.Timestamp.now() + pd.Timedelta(minute_departure_cap, "min")
    ]
