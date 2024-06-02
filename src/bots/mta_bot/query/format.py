from typing import List, Tuple

import pandas as pd


def format_html(stop_name: str, direction: str, train_schedule: List[Tuple[str, pd.Timestamp]]):
    direction_description = {
        "N": "Uptown/Queens",
        "S": "Downtown/Brooklyn",
        "U": "Uptown/Queens",
        "D": "Downtown/Brooklyn",
    }[direction]
    html_content = [f"{stop_name} \n<b>{direction_description}</b>", "-------------------------------"]
    tnow = pd.Timestamp.now().tz_localize(None)
    for route, arrival_time in train_schedule:
        waiting_time_minute = int((arrival_time - tnow) / pd.Timedelta("1 min"))
        html_content.append(f"{route} <b>{waiting_time_minute} min</b>@ {arrival_time.strftime('%H:%M')}")
    return "\n".join(html_content)
