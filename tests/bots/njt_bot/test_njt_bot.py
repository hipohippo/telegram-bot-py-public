import pytest
import nodriver as uc
import bs4
from bs4 import BeautifulSoup
from bots.njt_bot.query.bus_and_stop import NJTBusStop
from bots.njt_bot.query.bus_api import next_bus_job
from bots.njt_bot.query.path import html_format_path_status_output, get_train_status, PathStation


class TestNJTBot:
    def test_path_query(self):
        station_query = "hoboken"
        station_map = PathStation.get_station_map()
        current_station = station_map.get(station_query)
        path_train_status = html_format_path_status_output(current_station, get_train_status(current_station))
        print(path_train_status)

    @pytest.mark.asyncio
    async def test_browser_and_parser(self):
        browser = await uc.start()
        stop = NJTBusStop.RWNY
        tab1 = await browser.get(f"https://mybusnow.njtransit.com/bustime/wireless/html/eta.jsp?route=All&id={stop.id}&showAllBusses=on")
        await next_bus_job(NJTBusStop.RWNY, "NJ", browser)