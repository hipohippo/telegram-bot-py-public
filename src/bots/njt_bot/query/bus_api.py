"""
projecte parked due to anti-robot mechanism on njtransit.com
"""
import re
from typing import List

from bs4 import BeautifulSoup
from nodriver.core.browser import Browser

from bots.njt_bot.query.bus_and_stop import NJTBusStop, NextBus, format_bus_message


async def extract_content_from_page(stop: NJTBusStop, browser: Browser) -> BeautifulSoup:
    tab1 = await browser.get(
        f"https://mybusnow.njtransit.com/bustime/wireless/html/eta.jsp?route=All&id={stop.id}&showAllBusses=on"
    )
    page_body = await tab1.query_selector("body")
    page_content = await page_body.get_html()
    return BeautifulSoup(page_content, features="lxml")


def parse_content_from_page(page_content: BeautifulSoup) -> List[NextBus]:
    scheduled_bus_and_arrivals = page_content.find_all("strong", attrs={"class": "larger"})
    capacity = page_content.find_all("span", attrs={"class": "smaller"})
    bus_and_prediction = [element.text.replace("\xa0", "") for element in scheduled_bus_and_arrivals]
    vehicle_info = [re.sub("[\n\t\xa0]", "", cap.text) for cap in capacity]

    num_arrival_info = len(bus_and_prediction) // 2
    return [
        NextBus(bus_and_prediction[2 * i], bus_and_prediction[2 * i + 1], vehicle_info[i])
        for i in range(num_arrival_info)
    ]


async def next_bus_job(stop: NJTBusStop, direction: str, browser: Browser) -> str:
    page_content: BeautifulSoup = await extract_content_from_page(stop, browser)
    bus_arrivals = parse_content_from_page(page_content)
    message = format_bus_message(stop, bus_arrivals, direction)
    return message
